---
status: Draft
maintainer: pacoxu
date: 2026-09-17
last_updated: 2026-09-17
tags: kubernetes, kep, sig-node, dynamic-containers, in-place-resize, agent-sandbox, ai-infrastructure
canonical_path: docs/blog/2026-09-17/2026-09-17-kep-5972-dynamic-containers_zh.md
source_urls:
  - https://github.com/kubernetes/enhancements/issues/5972
  - https://github.com/kubernetes/enhancements/pull/6169
  - https://github.com/kubernetes/enhancements/issues/2837
  - https://github.com/kubernetes/enhancements/issues/5474
  - https://github.com/kubernetes-sigs/dra-driver-cpu
  - https://kep.k8s.io/1287
  - https://kep.k8s.io/5474
  - https://kubernetes.io/blog/2025/12/19/kubernetes-v1-35-in-place-pod-resize-ga/
---

# KEP-5972 Dynamic Containers：把十年不变的 Pod 容器列表改成动态执行信封

> **合并前快照。** 本文按 **2026-09-17** 排期写作，KEP 正文核对到
> [tallclair/k8s-enhancements@`d53aad1c`][kep-snapshot]
> （[kubernetes/enhancements#6169](https://github.com/kubernetes/enhancements/pull/6169)
> 仍 open，带 `do-not-merge/hold`）。KEP 正式合入 `kubernetes/enhancements`
> 后，应以合并版本复核 API 细节，再把本页从 Draft 改为可发布状态。

## 先说结论

`KEP-5972 Dynamic Containers` 要改的不是一个新 CRD，而是 Kubernetes 用了十年的
核心假设：**运行中的 Pod 主容器列表 `.spec.containers` 不可变。**

它允许在 Pod 已经 `Running` 之后，通过专用 subresource `pods/dynamic`
增删 **main container**。调度、sandbox、CNI、卷和设备初始化可以提前完成；真正要跑的
workload 稍后再注入。Kubelet 把这次变更当成一次 **原子 allocation**，语义对齐
In-Place Pod Resize。

这就是颠覆点：Pod 不再只是“一组创建时就写死的容器”，而变成一块
**Resource Envelope（资源信封）**。Kubernetes 负责 L1 放置和配额边界，Ray /
Slurm / Agent runtime 可以在信封内部做 L2 细粒度调度。

1.37 enhancements freeze 没有放行它。争议从 **6 月 12–13 日 SIG Architecture
邮件列表** 就开始了：不是“方向错了”，而是 **改十年行为的 KEP，留给社区评论的
时间不够**。Dawn Chen 先在邮件里揽下 timing 责任、争取默认关闭的 Alpha；freeze
后在 exception 上回避自己做最终 SIG 签字，并把时间线说清楚：这不是五天临时起意，
而是多年 node primitive 改造的收口。

## 1. KEP 揭秘：它做了什么

### 1.1 一句话

Dynamic Containers 让 **main container 可以在 Pod 运行时被加入和移除**。
调度、初始化和 workload 执行被拆开，Pod 从静态容器列表变成高 churn、低延迟的
执行信封。

目标写得很具体：

- 把 Pod 创建、调度、初始化从 workload 执行路径上拆出去，支撑 warm pool
- 支持高频增删容器
- 把“请求到开始执行代码”往 **sub-100ms** 推

明确不做的事同样重要。当前草案把范围压在 **Pod update 行为**，后续再用独立 KEP
补：

- 不引入新的 Pod phase / state
- 不做动态卷管理（只能挂已经挂好的卷）
- 不做 running Pod 上的 mutable ResourceClaim（“dynamic DRA”）
- **不提供绕过 kube-apiserver 的旁路 mutation**
- 不改 Pod 创建路径

最后这一条值得单独标出来。2026-03 的 enhancement issue 标题还是
*Optimistic Execution*：Kubelet 先在本地注入容器，再异步回写 API。当前 KEP 已经把
这条路写成 Non-Goal。社区要改的是 Pod 可变性，不是绕过 admission 的快路径。

### 1.2 为什么现在做

动机只有两条，都对着 AI / HPC，而不是通用微服务。

**分层调度。** Kubernetes 做 L1：全局放置（例如 PodGroup）并守住安全的资源信封。
Raylet / Slurmlet 这类框架控制面做 L2：在信封里切 CPU/Memory、管 sub-cgroup、
拉起短生命周期任务。不必每次 spawn 都再走一遍 kube-scheduler。

**解耦运行时初始化。** 延迟敏感 workload 可以先把这些成本付掉：

- 调度和资源分配
- `RunPodSandbox` 和 CNI
- 卷挂载与初始化
- 设备挂载与初始化
- InitContainer 做的应用级准备

之后再往已经热好的 Pod 里加 worker 容器。KEP 认为，这是交互式 agentic
workload 逼近 sub-100ms 的关键，而不是把普通 Pod 启动再优化几个百分点。

四个官方 user story 也止于此，没有往产品层展开：

| 场景 | 做法 | KEP 写的价值 |
| --- | --- | --- |
| 自治框架治理（Ray、Slurm） | 框架控制面当 Local Pod Controller | 低延迟 spawn，且不必回调 kube-scheduler |
| Agent warm pool | 预分配 Pod，再注入短命工具沙箱 | 绕过创建、调度、初始化 |
| Restore / migration fast-path | 目标节点先放 shell Pod，再 restore 进壳 | 恢复到秒级以下 |
| Sidecar / daemon 原地升级 | 抽换辅助容器 | 少中断；某些情况可蓝绿 |

### 1.3 API 长什么样

草案 **不加新字段**。API 变化收在两个 subresource：

1. **`pods/dynamic`**：新的 update 入口。除了主资源已经允许的变更（镜像、
   grace period 等）和 `/resize` 已允许的 resize，这里还可以增删
   `.spec.containers`。
2. **`pods/allocated`**：只读。按需从 kubelet 的 `/allocatedPods` 取
   **已经 allocation 成功** 的 Pod spec，不在 apiserver 再存一份。

`/dynamic` 的权限 **不进默认 `edit` ClusterRole**，必须由 cluster-admin
显式授予。一次请求可以同时加、删多个容器；走标准 Pod validation，再叠加下面的
限制。容器名必须在所有 container **以及所有 container status** 里唯一；
`.spec.containers` 不能删空；`DeletionTimestamp` 一旦打上，就不能再改容器集合。

`/resize` 继续保留，用来表达“只许改资源、不许改正在跑的代码”。以后若要做动态卷
之类的更大可变性，也计划挂到同一个 `/dynamic` 上。集群可以用 apiserver 静态参数
`--disable-pod-subresources` 关掉。

为什么还要 `/allocated`：desired spec（etcd 里的 Pod）和 allocated spec（kubelet
本地）可以长时间分叉。In-Place Resize 当年是把已分配资源镜像进 Pod status。这次
可变面大会急剧撑大对象；再为每个 Pod 复制一份 `AllocatedPod` 也会把对象数量打爆。
所以 allocated 视图改成 kubelet 现场提供。

### 1.4 增删容器实际怎么走

新增容器的 allocation **和 in-place resize 同一条路**。给新容器加资源，就是一次
Pod resize，可能 `Deferred`，也可能 `Infeasible`。一次请求里的加、删必须
**全部能分配才生效**。allocation 会 checkpoint **完整 container spec**。

状态机很短：

- 已加入但还没分配：`ContainerStatus` 为 `Waiting`，reason 是 `Unallocated`
- 已分配：下一次 pod sync 里 `UpdatePodFromAllocation` 改 spec，kubelet 发现新
  容器没在跑就拉起
- 已从 allocation 拿掉但仍在跑：保持 `Running`，直到 `killContainer`（尊重
  grace period）
- 终止后 status 先留着，再 GC：最多保留约 10 条已移除 status，并和现有
  container GC 对齐清日志

镜像更新也被收进这条原子 allocation。今天可以出现：resize 还在 Deferred，镜像却
已经重启成新 image。feature gate 打开后，镜像更新也要等整次变更可分配。KEP 把这
当成修正，不是附带破坏。

Probe manager 也要从“Pod 创建时一次性装探针”改成“容器启动时装、终止时拆”。新容器
带 readiness probe，会先把整个 Pod 打成 unready。

### 1.5 Alpha 边界

这些限制被写成“第一版为了缩小范围”，不是永久物理定律：

- 只能增删 main container，不能动 init container
- Pod 必须已经 `Running`，且 init 全部完成
- 不做通用 container mutation：同名容器必须先彻底移除，才能再加回来
- 不能改变 Pod QoS；BestEffort Pod 上新容器不能带 resource requirements
- 新容器只能挂 Pod 里已经有的 volume / ResourceClaim
- 资源类型受 in-place resize 能力约束；Windows、开了 swap 的 Pod 不行
- 不能加 privileged 容器
- 新容器不能用 HostPort
- 至少保留一个 main container
- 进入 terminating 后停止 allocation

Admission 用 **fail-closed**：如果某个 webhook / policy 会拦 `pods` 的 CREATE
或 UPDATE，但没有覆盖 `pods/dynamic`，则 `/dynamic` 请求直接拒绝。Selector 会算
进匹配，`MatchConditions` 不算。目的是：老策略没升级，就不能从新入口绕过去。

内置 admission 也要接这条路径，至少包括 `PodSecurityAdmission`、
`PodResizeValidator`、`LimitRanger`、`NodeDeclaredFeatures`、`ResourceQuota`。

## 2. 颠覆的点

KEP 自己的 Drawbacks 写得很直：改 `.spec.containers` 等于推翻生态里
“Pod 是不可变执行信封”的长期假设。下面按影响面拆，不往外扩。

### 2.1 十年假设被打开：主容器列表不再是创建时的常量

Kubernetes 对外一直有一条近似定律：要换主容器，就删 Pod 重建。镜像可变、
ephemeral container 可变、后来资源也可以 `/resize`，但 **容器集合本身** 不行。

这次动的是集合，不是某个字段。Deployment、Job、mesh injector、日志 sidecar、
按 container name 抓指标的 HPA/VPA，很多都默认 `.spec.containers` 在 CREATE
之后是闭集。KEP 把风险写进正文：只看 CREATE 缓存的 controller 可能漏掉新容器、
索引越界，或来不及注入 sidecar。

缓解不是“大家以后注意”，而是：

- feature gate `DynamicContainers` 默认不改现有行为
- 变更只能走 `/dynamic`，默认 `edit` 没有这个 verb
- 老 admission 没覆盖新 subresource 就 fail-closed

也就是说：**默认宇宙仍是静态 Pod；可变性必须带着明确 intent 进来。**

### 2.2 Pod 语义从“静态工作单元”变成“资源信封”

Issue [#5972](https://github.com/kubernetes/enhancements/issues/5972) 的原题是
*Dynamic Pod Mutation*，摘要把 Pod 叫做 **Fluid Execution Environment**。KEP
正文收敛成一句话：Pod 是 Kubernetes 分配出来的 Resource Budget，容器生命周期
可以在预算内部流动。

这比 in-place resize 更进一步。Resize 改的是信封里已有容器的 CPU/Memory；
Dynamic Containers 改的是 **信封里有哪些执行体**。Warm pool、shell Pod restore、
框架在节点上 spawn 任务，都建立在这个新语义上。

KEP 也解释了为什么不走两条更“像那么回事”的替代：

- **只把普通 Pod 启动优化到 100ms**：付不掉 InitContainer、预拉模型、sidecar
  数据库、凭证交换这些跨 Pod 很难协调的成本。
- **扩大 ephemeral containers**：它是 `kubectl debug` 语义。启动顺序在 init
  完成前、不计入 `keepCount`、不参与 Pod phase/readiness/QoS，RBAC 也是给人排障
  用的。拿它跑生产 workload，会把 debug 权限和自动化编排权限缠在一起。

所以颠覆不是“多一个可以变的容器类型”，而是 **main container 进入可变面**。

### 2.3 调度职责下沉：Kubernetes 守边界，框架在节点上微调度

L1/L2 不是新名词，但第一次直接改 node 上的容器集合来兑现：

```text
L1  kube-scheduler / PodGroup     放信封、守配额和隔离
L2  Ray / Slurm / Agent runtime   在信封内增删容器、切 sub-cgroup
```

对 AI-Infra 来说，这意味着一批今天只能活在 CRI 旁路、pause 容器或自定义 sandbox
CRD 里的能力，被讨论成 **kubelet 正规 reconcile 循环的一部分**。KEP 仍要求变更
经过 apiserver；它没有把控制面从关键路径上拿掉，只是拿掉了“每次都创建新 Pod、
再调度、再初始化”。

### 2.4 安全边界从“扩 Pod UPDATE”改成“新 subresource”

1.37 freeze 前后真正引发 SIG Auth / API review 的，不是 warm pool 故事，而是：
**如果走标准 Pod UPDATE，现有生态的可变性假设和 admission 边界会被一次性打穿。**

作者把新 mutability 收到 `/dynamic` 之后，还加了两层：

- 默认 RBAC 不给
- fail-closed：拦 CREATE/UPDATE 的策略必须同时拦 `/dynamic`

SIG Auth 讨论里还有一条更长远的声明：如果已经要打破 Pod 可变性假设，就只破一次。
`/dynamic` 把 **任意 Pod 字段的未来 mutation** 都划进范围内——不等于 alpha
全开，但政策控制器必须把 `/dynamic` 上的请求当成完整 Pod 重新评估。

Dawn 在 freeze exception 里把这次转向概括为：从标准 Pod UPDATE，转到需要
**显式可变 intent** 的专用 subresource，从而默认把爆炸半径卡住，让普通
controller 行为不变。

需要把时间线说准确：Dawn 当时的表述还包括 **Pod 创建时声明可变性**。当前草案
**还没有**加这个字段。Beta graduation 里明确留了作业：
“是否在创建时用字段标记 dynamic / non-dynamic”。Alternatives 里作者更倾向继续用
RBAC 和 ValidatingAdmissionPolicy，理由是 `mutable: false` 无法兼容今天已经可变
的镜像、资源、ephemeral container，三态字段又容易把范围吵散。2026-09-15
`@deads2k` 的 review 仍在问 opt-in 字段。合并前这是未收口点。

### 2.5 生态和可扩展性会被一起拖进来

KEP 自己点名的冲击：

- 第三方 controller 若假定容器静态，必须改成 reconcile UPDATE
- 短生命周期容器会放大 Pod status PATCH，打 kubelet status manager、apiserver
  和 etcd；本 KEP 不直接解决，只提到 1.37 已在探索 init container 的 status
  coalescing
- HPA/VPA 按 container name 抓指标时，目标容器可能被动态删掉
- Cluster Autoscaler / Karpenter 应看聚合资源，行为接近 in-place resize；资源变化
  来自新容器、旧容器 resize 还是 Pod-level resize，对它们应无差别

Alpha SLO 写的是：排除拉镜像且资源足够时，动态加容器到 `Running` 的额外开销
**< 500ms**。这和动机里的 sub-100ms 不是同一段：前者是 kubelet 路径开销目标，
后者是端到端交互目标。

## 3. 准备工作，以及 1.37 花絮

### 3.1 这不是一个突然出现的 node 功能

Enhancement issue 由 Dawn Chen 在 **2026-03-23** 打开，明确写在
`go/k8s-for-batch` 路线上，并点出 1.35 前后已经 GA 或成型的地基：

- [KEP-1287 In-Place Pod Resize][ippr-ga]
  （1.35 GA）：`/resize` 让 CPU/Memory 可原地改。Dynamic Containers 的 allocation
  直接复用这条路。
- [KEP-2837 Pod-level resources](https://github.com/kubernetes/enhancements/issues/2837)：
  把信封做成统一预算，而不是只按单个容器加总。Dawn 在 SIG Arch 邮件里把它和
  writable cgroups、CPU DRA 并列，写成这条能力的地基。
- [KEP-5474 Writable cgroups](https://kep.k8s.io/5474)：让框架控制面在自己的
  cgroup 子树里做细粒度隔离，对应 L2 微调度。
- [DRA CPU driver](https://github.com/kubernetes-sigs/dra-driver-cpu)：把 CPU
  分配从 kubelet CPUManager 挪到 DRA，信封内部的 CPU 拓扑才有下一层语言。

KEP metadata 的 `see-also` 目前只链了 1287，但 issue 和 SIG Arch 邮件把这些
写成同一条多年线：先让信封里的资源可调、cgroup 可写、CPU 可 DRA 化，再打开容器
集合本身。

公开时间线也很清楚：

| 日期 | 事件 |
| --- | --- |
| 2026-03-23 | Issue [#5972](https://github.com/kubernetes/enhancements/issues/5972) 打开，标题还是 Optimistic Execution |
| 2026-04-30 | 设计文档提交 SIG Node 评审；KEP 写明有 Red Hat、Intel、NVIDIA、Uber 等维护者参与 |
| 2026-06-07 / 06-08 | `kep.yaml` 创建；[PR #6169](https://github.com/kubernetes/enhancements/pull/6169) 把文档改写成 KEP |
| 2026-06-09 | PRR freeze；问卷补齐后过了 PRR，但仍 *At risk for enhancements freeze* |
| 2026-06-12 | Tim Allclair 把 KEP 提到 SIG Architecture 邮件列表；下一次 SIG Arch 会在 freeze 之后 |
| 2026-06-13 | Michael Taufen 问 admission 缺口；David Eads 反对“来不及开会就催合入”；Dawn 回信揽下时机责任 |
| 2026-06-15 | 设计改到 `/dynamic` subresource；默认 `edit` 不授权 |
| 2026-06-16 | `@enj`、`@deads2k` 在 PR 上 `/hold`：改十年行为，五天不够评审 |
| 2026-06-16 AoE / 06-17 UTC | 1.37 enhancements freeze |
| 2026-06-17 | Enhancements 团队宣布未达标；三天内可补 exception。SIG Auth 讨论产出 fail-closed |
| 2026-09-08 | `@haircommander` `/milestone v1.38`，重新 lead-opted-in |

### 3.2 1.37 花絮：完整讨论史

1.37 的争议发生在两个地方，时间上是连续的。

- **6 月 12–13 日**：SIG Architecture 邮件列表，6 封信。主题是
  *KEP-5972: Dynamic (mutable) Containers*。先发到已弃用的
  `kubernetes-sig-architecture@googlegroups.com`，John Belamaric 要求改到
  `sig-architecture@kubernetes.io`。
- **6 月 15–17 日**：KEP PR 上的 `/dynamic` 转向、`/hold`、enhancements freeze
  未达标，以及 Dawn 在 exception 上回避 SIG 终签。

邮件线程决定了后面 PR 上所有人的语气。freeze 被叫停，不是评审者突然看见一份
陌生 KEP，而是 SIG Arch 已经明确拒绝“来不及开会，请在邮件里讨论并优先合入”。

#### 6 月 12 日：Tim 把 KEP 提到 SIG Arch

Tim Allclair 的开场很克制：主容器列表要在运行时可变；实现主要复用 in-place
pod resize，**净代码量其实不大**；真正的担心是生态工具假定容器永不变化，这件事
会作为 Beta graduation 的主动调研和 outreach。然后是那句后来被抓住的话：

> The next SIG-Arch meeting isn't until after KEP freeze, so please comment on
> the KEP or respond here with any questions or concerns.

对作者来说，这是 freeze 前争取跨 SIG 可见性。对 SIG Arch 来说，这读起来像：
会开不成了，请把讨论收进这封邮件，并给合入让路。

#### 同一线程里的技术问题：CREATE-only 策略怎么办

Michael Taufen 问：以前只在 Pod CREATE 上跑的安全策略，要不要在 UPDATE 上自动
再跑一遍，免得打开这个功能后出现 policy gap？

Tim 当时的缓解只有三条，而且明确说 **没法强迫第三方 admission**：

1. 第一方控件（例如 PodSecurityAdmission）会补覆盖
2. 动态加的容器不能 escalate SecurityContext（当时 KEP 里还有
   *No SecurityContext Escalations* 一节）
3. release notes 和社区沟通

这和今天草案里的 fail-closed 不是同一套。6 月 13 日作者还认为第三方 webhook
不会被强制改；4 天后 SIG Auth 才把规则反过来：拦 `pods` CREATE/UPDATE 的策略
必须同时拦 `/dynamic`，否则直接拒绝。deads2k 后来在 PR 上说“过去五天设计还在
大幅改”，指的就是这类边界，不是 user story 在变。

#### 6 月 13 日：deads2k 反对的是节奏

David Eads 连发两封，论点没有混：

- 没赶上 SIG Arch 会，不能当成把超大架构变更塞进本周期的理由
- “开晚了，请把讨论限制在这封邮件并优先合入”，不符合过去十年的共识建设
- SIG 会通常两周一次，这种量级至少该留 **一个月** 评论，而不是五个工作日
- 另外一条独立担心：Beta 必须要求主流生态项目能容忍这个变化，才能默认打开

Tim 的回复是：Beta 里已经有
“Ecosystem research & outreach for static container assumptions”，可以写得更硬；
和 Derek Carr 正在讨论用 **RBAC subresource** 做更明确的 opt-in；SIG Arch 流程
问题交给 Dawn。

#### Dawn 的第一封信：时机责任在我，Alpha 还是要进这个周期

6 月 13 日 06:40，Dawn 写给 David 和 SIG Architecture 的信，和后来 exception
上的回避信不是同一封。这封的核心是 **揽责任 + 争 Alpha 门票**。

她先把 timing 揽下来：是她建议 Tim 以 **默认关闭的 Alpha** 抢这个 release，而不是
先做一轮很长的跨 SIG 预审。和 SIG Arch 的沟通缺口完全在她。

但她同时写明为什么不能等：

> With the current explosion of new AI-native and Agentic infrastructure, the
> community is facing an immediate choice: we must adapt the Kubernetes
> execution envelope to support these ultra-low-latency workloads now, or risk
> the industry building around us.

技术上，这封信把“不是突然转向”说得比 KEP 正文更完整：他们提前单独找过 SIG Auth、
SIG Node 维护者和若干 API reviewer；对 SIG Scheduling 的影响，已经在 in-place
resize 里讨论过。地基是 In-Place Pod Resize、writable cgroups、Pod-level
resources、CPU DRA driver。Derek 提出的安全/RBAC 隔离会被写进本 milestone：
**不要扩大标准 Pod UPDATE**，把能力收到需要显式 RBAC opt-in 的专用 subresource。

流程上，她用 Alpha 定义挡生产风险：feature gate 默认关；KEP 批了也可以在 1.37
停发，甚至发了还能撤。生态就绪已经是 Beta 硬门槛。她希望用即将到来的双周
SIG Arch 会打磨 graduation 和 outreach，同时保住这个周期的动量。

一句话：这封信承认 **跨 SIG 窗口不够**，但主张 **不够的部分用 off-by-default
Alpha 换**，不要把整个方向推到下个周期。

#### 随后三天：subresource、/hold、exception 回避

6 月 15 日，Tim 把新 mutability 收到 `/dynamic`，并写明默认 `edit` 不授权。这是
邮件里承诺给 Derek 的那一刀，也是 Dawn 第一封信里“本 milestone 要更新 KEP”的
兑现。

6 月 16 日，争议从邮件挪到 PR。`@enj` `/hold`：这种量级该用 1.37 周期征求反馈，
不是所有问题都该由 core Kubernetes 解决。`@deads2k` 再 `/hold`：KEP 出现在
freeze 前一周，改十年行为，牵动安全、admission 和 SIG Apps；过去五天设计还在
大改，第一刀形状不稳，按会议节奏至少再留四周。实验可以在 branch 上做，不必先改
`main`。

1.37 enhancements freeze 要求 KEP 已经合入 `k/enhancements`。#6169 未合并，
轨道被摘掉。随后的 exception 窗口里，Dawn 写了 **第二封信**：她作为 SIG Node
lead 回避自己做最终 SIG 签字，把决定交给 Derek Carr、Mrunal Patel、Peter Hunt，
并把时间线钉死：

> The Timeline: This KEP was opened 9 days prior to the freeze, not 5. It is
> the direct output of a comprehensive design specification introduced and
> reviewed within SIG Node a month and a half ago with active participation
> from maintainers across multiple companies (including Red Hat, Intel, Nvidia,
> and Uber etc.). This work represents the logical culmination of a multi-year
> effort to adapt node primitives for modern AI/HPC infrastructure (including
> In-Place Pod Resizing, writable cgroups, and DRA CPU drivers) that has been
> actively socialized across multiple KubeCon cycles.
>
> The Design State: ... When senior API and Node reviewers raised critical
> concerns regarding the standard Pod UPDATE boundary, the authors actively
> collaborated to pivot the design to a dedicated API subresource requiring
> explicit mutability intent at Pod creation time. This community-driven pivot
> fundamentally bounds the blast radius by default, ensuring zero behavioral
> impact on standard ecosystem controllers.

申请的 3 天延期，是为了赶上下一次双周 SIG Arch 会，把 subresource 架构正式写进
KEP。6 月 17 日 SIG Auth 会又补上 fail-closed：第三方策略不覆盖 `/dynamic` 就
拒绝，直接回答了 Taufen 在邮件里提出、Tim 当时认为“强迫不了”的问题。

**Release Team / SIG Arch 叫停的是节奏，不是方向。** 邮件线程里双方其实已经把
分歧写清：作者侧认为 Alpha 默认关、可以随时停，应该进 1.37 换真实反馈；Arch /
Auth 侧认为改十年假设必须先有足够长的跨 SIG 评论窗，不能用“会开在 freeze 后”
把社区讨论压成五天邮件。最终 1.37 没有给 alpha 门票。KEP 带着 `/dynamic`、
fail-closed 和 `/allocated` 继续评，并改瞄准 1.38。

### 3.3 设计收口之后，代码铺垫已经开始

即使 KEP 没进 1.37，#6169 上已经能看到配套 PR：

- [`kubernetes/kubernetes#140659`](https://github.com/kubernetes/kubernetes/pull/140659)：
  Pod `/allocated` subresource
- [`kubernetes/kubernetes#140856`](https://github.com/kubernetes/kubernetes/pull/140856)：
  kubelet `/allocatedPods`
- [`kubernetes/kubernetes#141039`](https://github.com/kubernetes/kubernetes/pull/141039)：
  allocation checkpoint 改存完整 PodSpec

这和 KEP 的 Upgrade 策略一致：feature gate 打开不会改现有 Pod 行为，直到有客户端
真正打 `/dynamic`；关掉则拒绝新的结构变更，kubelet 继续跑最后一份 spec。Checkpoint
会升版本，字段名必须避开旧 schema，避免反序列化冲突。Kubelet 通过
NodeDeclaredFeatures 声明能力，update 路径按节点能力门控。

## 事实校对

| 项目 | 状态（2026-09-17） |
| --- | --- |
| KEP 编号 | `KEP-5972` |
| 名称 | Dynamic Containers |
| Issue | [kubernetes/enhancements#5972](https://github.com/kubernetes/enhancements/issues/5972)，2026-03-23，`@dchen1107` |
| KEP PR | [kubernetes/enhancements#6169](https://github.com/kubernetes/enhancements/pull/6169)，2026-06-08，`@tallclair`，**未合并** |
| 本文核对的正文 | [tallclair/k8s-enhancements@`d53aad1c`][kep-snapshot] |
| metadata | `status: implementable`，`stage: alpha`，`owning-sig: sig-node` |
| 参与 SIG | apps、architecture、auth；issue 上还有 scheduling |
| Feature gate | `DynamicContainers`（`kube-apiserver` + `kubelet`） |
| 1.37 | PRR 问卷过了，enhancements freeze 未合并，milestone 被摘掉 |
| 当前瞄准 | 2026-09-08 起 `latest-milestone` 讨论转向 **v1.38**；`kep.yaml` 快照仍写着 v1.37 |
| 仍开放的设计点 | 创建时 dynamic opt-in 字段；Kubelet / Scheduler resize race 的 Beta 策略 |

## 参考资料

- [KEP-5972 issue：Dynamic Pod Mutation](https://github.com/kubernetes/enhancements/issues/5972)
- [KEP-5972 PR：Dynamic Containers](https://github.com/kubernetes/enhancements/pull/6169)
- [KEP 正文快照 `d53aad1c`][kep-snapshot]
- [kep.yaml 快照][kep-yaml-snapshot]
- [KEP-1287：In-Place Update of Pod Resources](https://kep.k8s.io/1287)
- [KEP-2837：Pod-level resources](https://github.com/kubernetes/enhancements/issues/2837)
- [Kubernetes 1.35：In-Place Pod Resize GA][ippr-ga]
- [KEP-5474：Writable cgroups](https://kep.k8s.io/5474)
- [kubernetes-sigs/dra-driver-cpu](https://github.com/kubernetes-sigs/dra-driver-cpu)
- [v1.37 enhancements freeze 通知](https://groups.google.com/a/kubernetes.io/g/dev/c/Tf0emFG0P_Q)
- [SIG Arch 邮件：Tim 提交 KEP-5972][sig-arch-tim]
- [SIG Arch 邮件：David Eads 反对 steamroll][sig-arch-deads]
- [SIG Arch 邮件：Dawn 揽下 timing 并争 Alpha][sig-arch-dawn]

[kep-snapshot]:
  https://github.com/tallclair/k8s-enhancements/blob/d53aad1c/keps/sig-node/5972-dynamic-containers/README.md
[kep-yaml-snapshot]:
  https://github.com/tallclair/k8s-enhancements/blob/d53aad1c/keps/sig-node/5972-dynamic-containers/kep.yaml
[ippr-ga]: https://kubernetes.io/blog/2025/12/19/kubernetes-v1-35-in-place-pod-resize-ga/
<!-- markdownlint-disable MD013 -->
[sig-arch-tim]:
  https://groups.google.com/d/msgid/kubernetes-sig-architecture/CALXpagwCBhzqiXp4jKRf5Dv5SMuw4auZQmtrhH5A9YeC2aUhtw%40mail.gmail.com
[sig-arch-deads]:
  https://groups.google.com/a/kubernetes.io/d/msgid/sig-architecture/CAFS1MjJfaZn2%2BTc%2BcvAA6gB%2B0bFLJ-5WWvcNZGMRKGCcZ99XyA%40mail.gmail.com
[sig-arch-dawn]:
  https://groups.google.com/a/kubernetes.io/d/msgid/sig-architecture/CAJo%3DGk44kY%3Dj42ev-Q0AyShbuXUGPjkVtAVRTjj6n4_z5xXq%3DQ%40mail.gmail.com
<!-- markdownlint-enable MD013 -->
