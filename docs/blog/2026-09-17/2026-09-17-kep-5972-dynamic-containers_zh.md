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

# KEP-5972 Dynamic Containers：运行中增删 Pod 主容器（草案）

> **合并前快照。** 本文按 **2026-09-17** 排期，KEP 正文核对到
> [tallclair/k8s-enhancements@`d53aad1c`][kep-snapshot]。
> [kubernetes/enhancements#6169](https://github.com/kubernetes/enhancements/pull/6169)
> 仍 open，带 `do-not-merge/hold`。功能未发布；合入后以合并正文和发行说明为准。

## 结论

运行中的 Pod 可通过 `pods/dynamic` 增删 **main container**。`.spec.containers`
在 CREATE 之后不再是闭集。

- 增删入口是 `pods/dynamic`；`pods/allocated` 只读，展示 kubelet 已分配规格
- allocation 复用 In-Place Pod Resize；一次请求里的增删全部可分配才提交
- 默认 `edit` 无 `/dynamic` 权限；admission **fail-closed**
- 1.37 未过 enhancements freeze；2026-09-08 起瞄准 **v1.38**

3 月 issue 标题仍是 *Optimistic Execution*（Kubelet 本地先注入，再异步回写
API）。当前草案把「绕过 kube-apiserver」写成 Non-Goal。改的是 Pod 可变性，
admission 仍走控制面。

## 1. 机制

### 1.1 范围

Pod 进入 `Running` 后，可增删主容器。调度、sandbox、CNI、卷、设备和
InitContainer 可以预先做完，再注入短生命周期 workload。目标是高频 churn，以及
「请求到开始执行」逼近 **sub-100ms**。

本阶段只改 **Pod update**：

- 不改 Pod 创建路径
- 不绕过 kube-apiserver
- 不做动态卷（只能挂已经挂上的卷）
- 不做 running Pod 上的 mutable ResourceClaim
- 不新增 Pod phase / state

后续更大的可变性（例如动态卷）计划仍挂在同一个 `/dynamic` 上。

### 1.2 动机与四个场景

面向 AI/HPC 低延迟，两条线并行：

**L1/L2 调度。** kube-scheduler / PodGroup 做放置和配额；Raylet / Slurmlet /
Agent runtime 在已分配的资源边界内切 CPU/Memory、管 sub-cgroup、拉起短任务，
不必每次 spawn 再走 kube-scheduler。

**解耦初始化。** 先付掉调度、`RunPodSandbox`、CNI、卷、设备、InitContainer，
再往热好的 Pod 里加 worker。普通 Pod 启动再快几个百分点，也付不掉这些跨 Pod
很难协调的成本。

| 场景 | 做法 | KEP 写的价值 |
| --- | --- | --- |
| Ray / Slurm | 框架控制面当 Local Pod Controller | 低延迟 spawn，不回调 kube-scheduler |
| Agent warm pool | 预分配 Pod，再注入短命工具沙箱 | 绕过创建、调度、初始化 |
| Restore / migration | 目标节点先放 shell Pod，再 restore | 恢复到秒级以下 |
| Sidecar / daemon 原地升级 | 抽换辅助容器 | 少中断；部分情况可蓝绿 |

扩大 `.spec.ephemeralContainers` 被明确否掉：那是 `kubectl debug` 语义——可在
init 完成前启动、不计入 `keepCount`、不参与 phase/readiness/QoS，RBAC 也是给人
排障用的。生产 workload 走 `pods/dynamic`。

### 1.3 API

草案不加新顶层字段，只加两个 subresource：

1. **`pods/dynamic`**：在主资源已允许的变更（镜像、grace period 等）和
   `/resize` 之外，增删 `.spec.containers`。一次请求可同时加、删多个容器。
2. **`pods/allocated`**：只读。按需从 kubelet `/allocatedPods` 取已分配 spec，
   不在 apiserver 再存一份对象。

权限不进默认 `edit` ClusterRole，需 cluster-admin 显式授予。标准 Pod
validation 仍然生效，再叠加 Alpha 限制。容器名必须在所有 container **以及所有
container status** 里唯一；`.spec.containers` 不能删空；
`DeletionTimestamp` 一旦打上，就不能再改容器集合。

`/resize` 保留：只许改资源、不许改正在跑的代码。集群可用
`--disable-pod-subresources` 关掉这类 subresource。

desired spec（etcd）和 allocated spec（kubelet 本地）可以长时间分叉。
In-Place Resize 当年把已分配资源镜像进 Pod status；这次可变面更大，镜像进
status 会撑爆对象，再复制一份 `AllocatedPod` 会打爆对象数量。所以 allocated
视图由 kubelet 现场提供。

### 1.4 增删路径

给新容器加资源，就是一次 Pod resize，可能 `Deferred` 或 `Infeasible`。一次
`/dynamic` 请求里的加、删及相关变更必须 **全部能分配才生效**。allocation
checkpoint **完整 container spec**。

- 已加入、未分配：`Waiting` / `Unallocated`
- 已分配：下次 pod sync 里 `UpdatePodFromAllocation` 改 spec，kubelet 拉起
- 已从 allocation 拿掉、进程仍在：保持 `Running`，再 `killContainer`（尊重
  grace period）
- 终止后 status 暂留，最多约 10 条已移除记录，再跟现有 container GC 清日志

镜像更新也进同一次原子 allocation：resize 还在 `Deferred` 时，新镜像不会先
单独落地。这是对现有「镜像更新与 resize 脱钩」的修正。

Probe 从「Pod 创建时一次性装」改成「容器启动时装、终止时拆」。新容器带
readiness probe，会先把整个 Pod 打成 unready。

内置 admission 要接 `/dynamic`，至少包括 `PodSecurityAdmission`、
`PodResizeValidator`、`LimitRanger`、`NodeDeclaredFeatures`、`ResourceQuota`。

### 1.5 Alpha 限制与 fail-closed

- 只动 main container，不动 init
- Pod 必须已 `Running`，且 init 全部完成
- 不做通用 container mutation：同名容器必须先彻底移除再加回来
- 不能改变 Pod QoS；BestEffort 上新容器不能带 resource requirements
- 新容器只能挂已有 volume / ResourceClaim
- 资源类型受 in-place resize 约束；Windows、开了 swap 的 Pod 不行
- 不能加 privileged 容器，新容器不能用 HostPort
- 至少保留一个 main container
- 进入 terminating 后停止 allocation

**fail-closed：** 若 webhook / policy 会拦 `pods` 的 CREATE 或 UPDATE，却没有
覆盖 `pods/dynamic`，则 `/dynamic` 直接拒绝。Selector 计入匹配，
`MatchConditions` 不算。旧策略没升级，就不能从新入口绕过。

## 2. 影响

### 2.1 `.spec.containers` 变成可变集合

镜像可变、ephemeral container 可变、资源可 `/resize`，主容器集合此前不行。
只看 CREATE 缓存的 controller、mesh injector、日志 sidecar、按 container name
抓指标的 HPA/VPA，可能漏掉新容器、索引越界，或来不及注入。

约束默认行为的四层：

- feature gate `DynamicContainers`
- 只走 `pods/dynamic`
- 默认 `edit` 无权限
- fail-closed admission

### 2.2 L1 守边界，L2 在节点上 churn

```text
L1  kube-scheduler / PodGroup     放信封、守配额和隔离
L2  Ray / Slurm / Agent runtime   在信封内增删容器、切 sub-cgroup
```

变更仍经 apiserver。省掉的是每次短任务都创建新 Pod、再调度、再初始化。

### 2.3 安全入口落在 `/dynamic`

1.37 期间，API / Node reviewer 反对扩大标准 Pod UPDATE。作者把新 mutability
收到 `/dynamic`。SIG Auth 进一步要求：若要打破 Pod 可变性假设，只破一次——
`/dynamic` 把 **任意 Pod 字段的未来 mutation** 划进范围（alpha 并未全开），
政策控制器必须把该请求当完整 Pod 重新评估。

Dawn 在 exception 信里写过「创建时显式声明可变 intent」。**当前草案没有这个
字段。** Beta graduation 才决定要不要加；Alternatives 里作者更倾向 RBAC +
ValidatingAdmissionPolicy。`@deads2k` 2026-09-15 仍在问
（[review](https://github.com/kubernetes/enhancements/pull/6169#discussion_r4018821540)）。

### 2.4 规模与指标

- 短生命周期容器放大 Pod status PATCH，打 kubelet status manager、apiserver、
  etcd；本 KEP 不直接解决，只提到 1.37 已在探索 init container status coalescing
- HPA/VPA 按容器名取数时，目标可能被动态删掉
- Cluster Autoscaler / Karpenter 看聚合资源，应与 in-place resize 同类

Alpha SLO：资源足够且不计拉镜像时，动态加容器到 `Running` 的额外开销
**< 500ms**。动机里的 sub-100ms 是端到端交互目标，两套数字不要混
（[KEP 正文][kep-snapshot]）。

## 3. 铺垫与 1.37 讨论

### 3.1 前置能力

Issue [#5972](https://github.com/kubernetes/enhancements/issues/5972) 于
**2026-03-23** 由 Dawn Chen 打开，写在 `go/k8s-for-batch` 上。地基：

- [KEP-1287 In-Place Pod Resize][ippr-ga]（1.35 GA）：`/resize` 与本次
  allocation 同路
- [KEP-2837 Pod-level resources](https://github.com/kubernetes/enhancements/issues/2837)：
  信封做成统一预算
- [KEP-5474 Writable cgroups](https://kep.k8s.io/5474)：L2 写自己的 cgroup 子树
- [DRA CPU driver](https://github.com/kubernetes-sigs/dra-driver-cpu)：CPU 从
  CPUManager 挪到 DRA

`kep.yaml` 的 `see-also` 目前只链 1287。SIG Arch 邮件把这四条写成同一多年线：
先让资源可调、cgroup 可写、CPU 可 DRA 化，再打开容器集合。

| 日期 | 事件 |
| --- | --- |
| 2026-03-23 | Issue [#5972](https://github.com/kubernetes/enhancements/issues/5972) 打开，标题 Optimistic Execution |
| 2026-04-30 | 设计文档进 SIG Node；Red Hat、Intel、NVIDIA、Uber 等维护者参与 |
| 2026-06-07 / 06-08 | `kep.yaml` 创建；[PR #6169](https://github.com/kubernetes/enhancements/pull/6169) 提交 |
| 2026-06-09 | PRR 问卷过了，仍 *At risk for enhancements freeze* |
| 2026-06-12 | Tim Allclair 把 KEP 提到 SIG Arch；下一次 SIG Arch 会在 freeze 之后 |
| 2026-06-13 | Taufen 问 admission 缺口；deads2k 反对催合入；Dawn 揽 timing、争 Alpha |
| 2026-06-15 | mutability 收到 `/dynamic`；默认 `edit` 不授权 |
| 2026-06-16 | `@enj`、`@deads2k` 在 PR `/hold` |
| 2026-06-16 AoE / 06-17 UTC | 1.37 enhancements freeze |
| 2026-06-17 | 未达标；SIG Auth 补上 fail-closed |
| 2026-09-08 | `@haircommander` `/milestone v1.38` |

### 3.2 SIG Arch 邮件（6 月 12–13 日，6 封）再接到 freeze

先发到已弃用的 `kubernetes-sig-architecture@googlegroups.com`，John Belamaric
要求改到 `sig-architecture@kubernetes.io`。

**6 月 12 日 Tim：** 主容器列表要在运行时可变；净代码量主要复用 in-place
resize；生态假定容器永不变化，作为 Beta outreach。随后一句被抓住：

> The next SIG-Arch meeting isn't until after KEP freeze, so please comment on
> the KEP or respond here with any questions or concerns.

**Michael Taufen：** CREATE-only 安全策略在 UPDATE 上会不会出现缺口。Tim 当时
只承诺三件事：第一方（如 PodSecurityAdmission）补覆盖；动态容器不能 escalate
SecurityContext（当时还有 *No SecurityContext Escalations*）；发公告。并写明
**没法强迫第三方 webhook**。fail-closed 是 6 月 17 日 SIG Auth 才反过来的。
deads2k 后来说「过去五天设计还在大改」，指的是这条边界。

**6 月 13 日 David Eads：** 没赶上 SIG Arch 会，不能当成把超大架构变更塞进本
周期的理由。「开晚了，请把讨论限制在这封邮件并优先合入」不符合过去十年的共识
建设。SIG 会两周一次，这种量级至少该留 **一个月**，不是五个工作日。Beta 必须
要求主流生态能容忍这个变化，才能默认打开。

Tim 回复：Beta 已有
“Ecosystem research & outreach for static container assumptions”；与 Derek
Carr 在谈 RBAC subresource opt-in；流程问题交给 Dawn。

**Dawn 第一封（6 月 13 日 06:40）：** 揽 timing——是她让 Tim 用默认关闭的
Alpha 抢这个周期，和 SIG Arch 的沟通缺口在她。方向判断写在同一封：

> With the current explosion of new AI-native and Agentic infrastructure, the
> community is facing an immediate choice: we must adapt the Kubernetes
> execution envelope to support these ultra-low-latency workloads now, or risk
> the industry building around us.

他们已单独找过 SIG Auth、SIG Node 和若干 API reviewer；Scheduling 影响在
in-place resize 里讨论过。Derek 的方案会写进本 milestone：不要扩大标准 Pod
UPDATE，收到需要 RBAC opt-in 的专用 subresource。Alpha 默认关，KEP 批了也能在
1.37 停发。她要用即将到来的双周 SIG Arch 会打磨 graduation，同时保住动量。

**6 月 15 日：** Tim 把 mutability 收到 `/dynamic`，默认 `edit` 不授权。兑现
给 Derek 和 Dawn 第一封信的承诺。

**6 月 16 日 PR `/hold`：** `@enj` 认为这种量级该用 1.37 周期征求反馈，不是
所有问题都该由 core Kubernetes 解决。`@deads2k`：KEP 出现在 freeze 前一周，
改十年行为，牵动安全、admission 和 SIG Apps；第一刀形状不稳，按会议节奏至少
再留四周。实验可以在 branch 上做，不必先改 `main`。

#6169 未合并，1.37 轨道被摘。exception 窗口里 Dawn 写了 **第二封信**：回避
自己做最终 SIG 签字，交给 Derek Carr、Mrunal Patel、Peter Hunt：

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

3 天延期是为了赶上下一次双周 SIG Arch 会，把 subresource 写进 KEP。6 月 17 日
SIG Auth 补上 fail-closed，回答了 Taufen 的问题。

作者侧主张：Alpha 默认关，进 1.37 换真实反馈。Arch / Auth 侧主张：改十年假设
必须先有足够长的跨 SIG 评论窗。1.37 没有给 alpha 门票。设计带着 `/dynamic`、
fail-closed、`/allocated` 继续评，改瞄准 1.38。

### 3.3 配套代码

#6169 讨论期已有：

- [`kubernetes/kubernetes#140659`](https://github.com/kubernetes/kubernetes/pull/140659)：
  Pod `/allocated`
- [`kubernetes/kubernetes#140856`](https://github.com/kubernetes/kubernetes/pull/140856)：
  kubelet `/allocatedPods`
- [`kubernetes/kubernetes#141039`](https://github.com/kubernetes/kubernetes/pull/141039)：
  allocation checkpoint 改存完整 PodSpec

gate 关闭时现有 Pod 行为不变；关掉 gate 则拒绝新的结构变更，kubelet 继续跑
最后一份 spec。Checkpoint 升版本，字段名避开旧 schema。Kubelet 经
NodeDeclaredFeatures 声明能力，update 按节点能力门控。

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
| 当前瞄准 | 2026-09-08 起讨论转向 **v1.38**；`kep.yaml` 快照仍写 v1.37 |
| 仍开放 | 创建时 dynamic opt-in 字段；Kubelet / Scheduler resize race 的 Beta 策略 |

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
