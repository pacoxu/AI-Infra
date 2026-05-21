---
status: Active
maintainer: pacoxu
date: 2026-05-21
tags: kubernetes, scheduler, scheduling-framework, sig-scheduling, workload-aware-scheduling
canonical_path: docs/blog/2026-05-21/2026-05-21-kubernetes-scheduler-framework-evolution_zh.md
source_urls:
  - https://github.com/kubernetes/enhancements/blob/master/keps/sig-scheduling/624-scheduling-framework/README.md
  - https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/
  - https://kubernetes.io/docs/reference/scheduling/policies/
  - https://kubernetes.io/docs/reference/scheduling/config/
  - https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/
  - https://github.com/kubernetes-sigs/scheduler-plugins
  - https://kubernetes.io/docs/concepts/scheduling-eviction/pod-scheduling-readiness/
  - https://kubernetes.io/blog/2022/12/26/pod-scheduling-readiness-alpha/
  - https://kubernetes.io/blog/2024/12/12/scheduler-queueinghint/
  - https://kubernetes.io/docs/concepts/workloads/pods/scheduling-group/
  - https://kubernetes.io/docs/concepts/workloads/podgroup-api/
  - https://kubernetes.io/docs/concepts/scheduling-eviction/gang-scheduling/
  - https://kubernetes.io/blog/2025/12/29/kubernetes-v1-35-introducing-workload-aware-scheduling/
  - https://kubernetes.io/blog/2026/05/13/kubernetes-v1-36-advancing-workload-aware-scheduling/
  - https://kubernetes.io/docs/concepts/scheduling-eviction/workload-aware-preemption/
  - https://kubernetes.io/docs/concepts/scheduling-eviction/topology-aware-scheduling/
---

# Kubernetes Scheduler 演进主线：从 Predicates/Priorities 到 Scheduling Framework，再到 Workload-Aware Scheduling

如果要写 `kube-scheduler` 的发展过程，我认为最值得抓住的不是逐版本罗列 feature，而是它的架构主线：调度器如何从一套内建算法，变成一个阶段化、可插拔、还能继续长出 workload 语义的框架。

文中状态信息核对时间为 **2026-05-21**。

## 先说结论

- 如果你要写 scheduler 发展过程，最值得抓的不是每个 feature，而是三次架构转向：
  1. `Predicates/Priorities + Extenders`
  2. `Scheduling Framework`
  3. `Workload-Aware Scheduling`
- 你给的这张图，最适合放在第二阶段，也就是 `v1.16` 到 `v1.20` 的“框架成型期”。
- 从官方状态看，Scheduling Framework 在 `v1.19` 已经 stable；但从写作叙事上，把 `v1.16` 到 `v1.20` 合并成一个“慢慢稳定下来”的阶段更顺手，因为核心 extension points、双循环模型、以及默认插件心智模型都在这段时间定型了。

这里要强调：上面这条“`v1.16-v1.20` 成型期”是**写作上的阶段划分**，不是 Kubernetes 额外定义的官方 feature gate 术语。

## 1. 在 framework 之前：为什么老 scheduler 越写越重

在 framework 之前，`kube-scheduler` 的主叙事是 `Predicates` 和 `Priorities`。官方文档现在仍保留着一个历史页面，明确写到：**在 Kubernetes `v1.23` 之前**，调度策略还可以通过 scheduling policy 来指定 predicates 和 priorities 流程。

这套模型并不是完全不能扩展，但问题越来越明显：

- 扩展点太少。
- Extender 是进程外调用，存在 JSON 编解码和 HTTP 往返开销。
- Extender 无法直接复用 scheduler cache。
- 一旦调度流程中途 abort，很难把外部分配状态优雅回滚。

`KEP-624` 的 motivation 写得很直接：scheduler 功能越来越多，代码越来越复杂，自定义 scheduler 也越来越难跟上 upstream 节奏。于是社区开始把问题从“再加几个判断函数”切换成“把调度器本身重构成插件框架”。

## 2. `v1.16` 到 `v1.20`：Scheduling Framework 成型

### 2.1 这是最关键的一次架构转向

`KEP-624` 给出的目标不是“加一个新插件”，而是把 `kube-scheduler` 改造成一个带 plugin API 的调度框架：

- `Alpha`: `v1.16`
- `Beta`: `v1.17`
- `Stable`: `v1.19`

KEP 里定义的核心结构到今天都还是 scheduler 的基础心智模型：

1. 一个 Pod 的一次调度尝试，被拆成 `Scheduling Cycle` 和 `Binding Cycle`
2. scheduling cycle 串行执行
3. binding cycle 可以并发执行
4. 功能不再硬编码在“核心主循环”里，而是挂到 extension points 上

### 2.2 你这张图应该怎么解读

<p align="center">
  <img src="https://raw.githubusercontent.com/kubernetes/enhancements/master/keps/sig-scheduling/624-scheduling-framework/scheduling-framework-extensions.png" width="980" alt="Kubernetes scheduling framework extension points">
</p>

*图片来源：`KEP-624 Scheduling Framework`*

这张图最值得强调的，不是插件名字，而是 **调度器被分层了**：

- 队列入口：`Sort`
- 调度主循环：`PreFilter -> Filter -> PostFilter -> PreScore -> Score -> NormalizeScore -> Reserve -> Permit`
- 绑定主循环：`PreBind -> Bind -> PostBind`

其中有三件事特别重要。

**第一，`Reserve` / `Permit` 把“先占位、再确认”变成了框架能力。**

这也是为什么 KEP 在 use cases 里直接提到 coscheduling / gang scheduling 可以借助 `Permit` 来实现。换句话说，今天很多人把 gang scheduling 视为 AI 和 batch 时代的新需求，但它在 framework 设计期就已经被当作目标场景考虑进去了。

**第二，`PreBind` 让调度与外部资源准备之间有了明确衔接点。**

KEP 直接拿 dynamic resource binding 和 topology-aware volume provisioning 举例。这个 extension point 后来对 DRA、设备准备、存储拓扑这类问题都很关键。

**第三，`CycleState` 和 `FrameworkHandle` 让多阶段插件真正可写。**

插件不只是“插进去跑一下函数”，而是可以跨 extension point 共享状态，并且访问 scheduler cache。这是 framework 相比 extenders 的质变点。

### 2.3 为什么我建议把 `v1.20` 也算进“成型期”

严格按 feature state 说，framework 在 `v1.19` 就已经 stable 了。

但如果是写演进过程，把 `v1.16` 到 `v1.20` 合成一个阶段更自然，原因有三个：

- `v1.16` 到 `v1.19` 是 KEP 定义的 `alpha/beta/stable` 路径；
- `v1.18` 到 `v1.20` 这几版里，越来越多调度能力开始直接以 plugin/profile 的方式进入日常配置；
- 从社区心智上看，到 `v1.20` 左右，这张“调度周期 + 绑定周期 + extension points”的图已经成为理解 `kube-scheduler` 的标准入口。

这里也要强调：这是一种**写作上的阶段划分**，不是官方额外定义的“`v1.20` 才稳定”。

## 3. `v1.21` 到 `v1.34`：framework 稳住之后，scheduler 开始不只是“选节点”

framework 稳定之后，后面的演进不再是“是否有插件架子”，而是这个架子开始承载更多层次的问题。

### 3.1 `v1.23`：旧 policy 路线退场，plugin/config 路线成为主线

如果你按版本写演进，`v1.23` 是一个适合点名的分界线。

官方 `Scheduling Policies` 文档明确写到：**在 Kubernetes `v1.23` 之前**，还可以通过 scheduling policy 配 `predicates` 和 `priorities`。这等于从侧面说明，到了 `v1.23`，scheduler 的公开配置主线已经不再是老 policy，而是 framework 对应的 config / plugin 模型。

这件事的重要性不在于“删了一个旧接口”，而在于：

- scheduler 的扩展模型正式从“规则拼装”转向“插件组合”；
- 后续新能力几乎都不再优先寻找 policy 表达方式；
- 写 scheduler 历史时，`v1.23` 很适合作为“旧世界基本收尾”的节点。

### 3.2 `v1.25`：`KubeSchedulerConfiguration v1` 稳定，`profiles` 进入标准配置心智

Scheduler Configuration 文档现在把 `profiles` 作为标准能力来讲：一个 `kube-scheduler` 实例可以同时运行多个 profile，不同 profile 可以有不同 plugin 组合，但共享同一个 pending queue。

同时，文档也明确标了 **`Scheduler Configuration` 在 `v1.25 [stable]`**。这意味着 framework 不只是内部架构稳定，连它的主要配置入口也稳定下来了。

这件事的意义不只是“配置更灵活”，而是：

- default scheduler 不再只能有一条固定 pipeline；
- 同一个二进制里可以容纳不同 workload 的调度策略；
- 调度差异开始更多通过配置和插件组合表达，而不是直接 fork scheduler。

再往后，配置里又增加了 `multiPoint`，用于一次性把同一个插件挂到多个 extension points 上。这个变化说明 framework 不只是“可扩展”，还在继续朝“可维护、可配置”演进。

### 3.3 `v1.26` 到 `v1.30`：`Gated Pod` / `Pod Scheduling Readiness` 让 `PreEnqueue` 真正变得有感知

如果你想按版本补“Gated Pod”这条线，最自然的写法是把它和 `PreEnqueue` 放在一起讲。

官方 feature gates 页面给出的时间线是：

- `PodSchedulingReadiness` `Alpha`: `v1.26`
- `Beta`: `v1.27-v1.29`
- `GA`: `v1.30`

对应的用户侧 API 是 Pod 的 `.spec.schedulingGates`。官方文档的表述很直接：通过设置或移除 `schedulingGates`，你可以控制一个 Pod 何时才算“准备好进入调度”。

这件事为什么值得单独写？因为它让 scheduler 的思维方式发生了一个变化：

- 以前默认是“Pod 一创建就进队列”
- 有了 `schedulingGates` 之后，可以先把 Pod 留在 `gated` 状态
- 等外部条件满足，再移除 gate，让 Pod 真正进入调度

而在 framework 这一层，对应的关键 extension point 正是 `PreEnqueue`。

官方 Scheduling Framework 文档现在把 `PreEnqueue` 放在最前面：只有所有 `PreEnqueue` 插件都返回 `Success`，Pod 才会进入内部 active queue；否则会停留在 scheduler 的内部 unschedulable / gated 路径上，而且不会立刻得到 `Unschedulable` condition。

所以如果你要把 `Gated Pod` 和 framework 串起来，最准确的一句话应该是：

> `Pod Scheduling Readiness` 不是“又一个 Pod 字段”，而是 scheduler 开始把
> “什么时候让 Pod 进入 active queue” 也当作一等能力来设计。

这比单纯讲 `Filter/Score` 更能体现 framework 后期演进的方向。

### 3.4 `v1.28` 到 `v1.34`：`QueueingHint` 把“何时重试”做成可编程能力

很多人第一次看 KEP 那张图，会以为 scheduler 的创新主要在 `Filter/Score/Bind` 这些阶段。但后续几年的一个重要变化是：**社区开始把“队列管理和重试时机”也纳入 framework 能力。**

现在官方 Scheduling Framework 文档里已经把下面几个点写成标准接口：

- `PreEnqueue`
- `EnqueueExtension`
- `QueueingHint`

其中：

- `Pod Scheduling Readiness` 在官方文档里已经是 **`v1.30 stable`**；
- `QueueingHint` 在官方文档里已经是 **`v1.34 stable`**。

这一条如果按版本展开，其实很有意思。官方 feature gates 页面给出的时间线是：

- `SchedulerQueueingHints` `Beta` 且默认开启：`v1.28`
- `Beta` 但默认关闭：`v1.29-v1.31`
- `Beta` 且再次默认开启：`v1.32-v1.33`
- `GA`: `v1.34`

Kubernetes 官方在 **2024-12-12** 发布的 `v1.32` 博文，专门把 `QueueingHint` 当作一次重要 scheduler 吞吐优化来介绍。这个时间线本身就说明：这不是简单的小优化，而是一个被反复打磨过的内部调度机制。

这背后代表 scheduler 的重心变化：

- 早期更关注“一个 Pod 如何选 node”
- 后来开始更关注“哪些 Pod 应该先别进 active queue”
- 以及“什么事件值得把 unschedulable Pod 重新激活”

这对大规模集群尤其关键，因为真正拖垮调度吞吐的，经常不是单次 `Filter` 算法，而是大量明知暂时不可调度的 Pod 不断 churn 队列。

### 3.5 out-of-tree plugin 生态开始成形

`kubernetes-sigs/scheduler-plugins` 仓库可以看作 framework 价值最直接的外化之一。它的 README 现在仍明确写着：这是一个 **基于 scheduler framework 的 out-of-tree scheduler plugins 仓库**。

里面长期承载过或仍承载着一类非常典型的 AI、batch、large-scale 调度诉求：

- `Coscheduling`
- `Capacity Scheduling`
- `Node Resource Topology`
- `Trimaran`（load-aware scheduling）
- `Network-Aware Scheduling`

这说明 framework 的作用不只是让 upstream 更好维护，也让社区有了一个不必直接 fork `kube-scheduler`、但又能持续试验复杂调度策略的中间层。

## 4. `v1.35` 到 `v1.36`：framework 开始长出 workload-level scheduling

如果前一阶段的关键词是“把 Pod 调度器做成插件框架”，那最近两版的关键词就是：**把单 Pod 调度框架继续往 workload 调度推进。**

### 4.1 `v1.35`：Workload API + 初版 gang scheduling + opportunistic batching

Kubernetes 官方在 **2025-12-29** 发布的
`Kubernetes v1.35: Introducing Workload Aware Scheduling`
里，把这一版定义成首批 workload-aware scheduling 改进：

- `Workload API`
- `GenericWorkload` feature gate `Alpha`
- `GangScheduling` feature gate `Alpha`
- `OpportunisticBatching` feature gate `Beta`
- 基于 Pod 框架构建的 `gang scheduling`
- `opportunistic batching`

这里最值得注意的一句话是：官方明确说这套初版 gang scheduling 是 **built on a Pod-based framework**。

也就是说，workload-aware scheduling 不是另起炉灶做第二个 scheduler，而是继续长在 Scheduling Framework 这条主干上。

如果你要按版本补充更细一点，这里还有一个很值得点出来的对象：**`schedulingGroup` / Pod 与 group 的显式关联关系**。

当前官方文档把 `Scheduling Group` 标成 **`Kubernetes v1.35 [alpha]`**。它的含义是：Pod 可以通过 `spec.schedulingGroup` 指向一个 `PodGroup`，从而不再只是“一个待调度 Pod”，而是“某个 group 的成员 Pod”。

这很重要，因为它意味着 scheduler 的输入语义开始变化：

- 以前 scheduler 看到的是“一个独立 Pod”
- 现在 scheduler 可以看到“一个属于 group 的 Pod”
- 后续 gang、topology-aware placement、workload-aware preemption 才有了稳定的原生挂载点

从写作上说，`v1.35` 可以被看成是 “**group identity 开始进入原生 scheduler 语义**” 的起点。

### 4.2 `v1.36`：从 Pod-based gang 走向 PodGroup scheduling cycle

Kubernetes 官方在 **2026-05-13** 发布的
`Kubernetes v1.36: Advancing Workload-Aware Scheduling`
里，进一步把这条线往前推了一大步：

- `Workload` 和 `PodGroup` API 解耦，进入 `scheduling.k8s.io/v1alpha2`
- `kube-scheduler` 增加新的 `PodGroup scheduling cycle`
- 引入第一批 `topology-aware scheduling`
- 引入 `workload-aware preemption`
- 为 workload 打开 `DRA ResourceClaim` 支持
- Job controller 开始接入这套 API

这里最应该强调的不是“又多了几个 alpha feature”，而是 **scheduler 的 extension points 本身被扩展了**。

当前的 Scheduler Configuration 文档已经把下面两个点列进 extension points：

- `placementGenerate`
- `placementScore`

这两个 extension points 只对 PodGroup scheduling 生效，用来生成和评估一整个 group 的 placement。也就是说，从 `v1.36` 开始，framework 不只是把一个 Pod 放到一个 node 上，而是开始把“一组 Pod 作为一个 placement 问题”来建模。

这点和你提到的 `PodGroup Scheduling` 是同一件事的核心：

- `v1.35` 还是“基于 Pod framework 做 gang”
- `v1.36` 则真正出现了 **PodGroup scheduling cycle**
- `PreEnqueue` 这类队列前置机制继续承担“在条件满足前先别进入 active queue”的挡板角色
- 一旦进入调度，真正的放置决策已经不再是单 Pod 逐个走，而是 group-aware 的 cycle

这是 scheduler 演进里非常关键的一个台阶。

这时你就能看出 framework 演进的真正价值了：

- 第一阶段：把单 Pod 调度拆成 stages
- 第二阶段：把 stages 变成可配置、可插拔、可控队列的 framework
- 第三阶段：在这个 framework 上继续长出“一次处理一个 `PodGroup` / workload”的原生能力

换句话说，scheduler 演进不是“插件越来越多”，而是 **调度对象本身在升级**：从 `Pod`，慢慢走向 `PodGroup / Workload`。

## 5. 如果你问“还有哪些变化值得补”，我会优先补这几条

如果你想把后续部分写得更完整，我建议优先补下面这些，而且它们基本都和你现在的主线兼容：

1. `v1.23`：老 `Scheduling Policies` 路线退出主舞台。
2. `v1.25`：`KubeSchedulerConfiguration v1` 稳定，`profiles` 成为标准配置入口。
3. `v1.26-v1.30`：`Pod Scheduling Readiness`，也就是你说的 `Gated Pod`。
4. `v1.28-v1.34`：`QueueingHint`，这是 `PreEnqueue/EnqueueExtension` 之后“何时重试”这条线的关键补丁。
5. `v1.35`：`Workload API`、`GangScheduling`、`OpportunisticBatching`、`schedulingGroup`。
6. `v1.36`：`PodGroup API`、`PodGroup scheduling cycle`、`placementGenerate/placementScore`、`topology-aware scheduling`、`workload-aware preemption`、`PodGroup resourceClaims`。

如果只想保留最强主线，不想把文章写散，我会把“还有哪些变化”压成两类：

- **队列侧变化**：`Gated Pod`、`PreEnqueue`、`QueueingHint`
- **工作负载侧变化**：`schedulingGroup`、`PodGroup scheduling`、`workload-aware preemption`

## 6. 如果你要写这篇文章，我建议的主叙事

如果重点放在 `scheduler framework`，最好的写法不是从 feature list 展开，而是用一句主线贯穿全文：

> Kubernetes scheduler 的演进，本质上是从“内建 predicates/priorities 规则引擎”，
> 走向“阶段化插件框架”，再走向“能原生理解 workload 的调度系统”。

按这个主线，你可以把全文压成五段：

1. **旧时代的问题**
   `Predicates/Priorities + Extenders` 为什么不够用。
2. **framework 的提出**
   `KEP-624` 想解决什么；为什么要拆成 scheduling cycle 和 binding cycle。
3. **`v1.16-v1.20` 成型期**
   用你这张图讲 extension points；强调 `Reserve/Permit/PreBind` 的长期价值。
4. **framework 如何接管队列前半段**
   `v1.25-v1.34` 的 `profiles`、`Gated Pod`、`PreEnqueue`、`QueueingHint`。
5. **framework 如何通向 workload-aware scheduling**
   `v1.35-v1.36` 的 `schedulingGroup`、`PodGroup scheduling cycle`、`topology-aware scheduling`、`workload-aware preemption`。

## 7. 一个可以直接拿去用的开头

如果你想更快起笔，可以直接用下面这段：

> 今天再看 Kubernetes scheduler 的演进，如果只按版本罗列 feature，很容易变成一份 release notes 摘要。更值得抓住的主线，其实是 `kube-scheduler` 的架构变化：它先是一个以内建 predicates 和 priorities 为核心的单体调度器，随后在 `v1.16` 到 `v1.19` 之间逐步长成 Scheduling Framework，把调度流程拆成一组可编排的 extension points；到了 `v1.35` 和 `v1.36`，这套 framework 又继续向 workload-aware scheduling 演进，开始原生理解 gang、PodGroup、拓扑约束与 workload 级抢占。也就是说，scheduler 这些年的核心变化，不只是“支持了更多策略”，而是“它终于从一个写死逻辑的调度器，变成了一套可以持续长出新调度语义的框架”。

## 参考

- [KEP-624: Scheduling Framework](https://github.com/kubernetes/enhancements/blob/master/keps/sig-scheduling/624-scheduling-framework/README.md)
- [Scheduling Framework 文档](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)
- [Scheduling Policies（`v1.23` 之前的 predicates/priorities 配置）](https://kubernetes.io/docs/reference/scheduling/policies/)
- [Scheduler Configuration / profiles / multiPoint](https://kubernetes.io/docs/reference/scheduling/config/)
- [Feature Gates（`PodSchedulingReadiness` / `SchedulerQueueingHints` / `GenericWorkload` / `GangScheduling` / `OpportunisticBatching`）](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)
- [scheduler-plugins 仓库](https://github.com/kubernetes-sigs/scheduler-plugins)
- [Pod Scheduling Readiness](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-scheduling-readiness/)
- [Kubernetes 1.26: Pod Scheduling Readiness](https://kubernetes.io/blog/2022/12/26/pod-scheduling-readiness-alpha/)
- [Kubernetes v1.32: QueueingHint Brings a New Possibility to Optimize Pod Scheduling](https://kubernetes.io/blog/2024/12/12/scheduler-queueinghint/)
- [Scheduling Group](https://kubernetes.io/docs/concepts/workloads/pods/scheduling-group/)
- [PodGroup API](https://kubernetes.io/docs/concepts/workloads/podgroup-api/)
- [Gang Scheduling](https://kubernetes.io/docs/concepts/scheduling-eviction/gang-scheduling/)
- [Kubernetes v1.35: Introducing Workload Aware Scheduling](https://kubernetes.io/blog/2025/12/29/kubernetes-v1-35-introducing-workload-aware-scheduling/)
- [Kubernetes v1.36: Advancing Workload-Aware Scheduling](https://kubernetes.io/blog/2026/05/13/kubernetes-v1-36-advancing-workload-aware-scheduling/)
- [Workload-Aware Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/workload-aware-preemption/)
- [Topology-Aware Workload Scheduling](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-aware-scheduling/)
