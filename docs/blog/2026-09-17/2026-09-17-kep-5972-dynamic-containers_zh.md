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

# KEP-5972 Dynamic Containers：让 Pod 在运行时增删主容器（草案解读）

> **合并前快照。** 本文按 **2026-09-17** 排期写作，KEP 正文核对到
> [tallclair/k8s-enhancements@`d53aad1c`][kep-snapshot]
> （[kubernetes/enhancements#6169](https://github.com/kubernetes/enhancements/pull/6169)
> 仍 open，带 `do-not-merge/hold`）。KEP 尚未正式合入
> `kubernetes/enhancements`，功能也还未发布。后续请以合并版本和发行说明为准。

## 先说结论

`KEP-5972 Dynamic Containers` 讨论的是 Kubernetes 的一个核心行为变化：
运行中的 Pod 可以通过 `pods/dynamic` 增删 **main container**。

本文关心四件事：

1. 新增和删除主容器通过 `pods/dynamic`；`pods/allocated` 只读，展示 kubelet
   侧已分配（allocated）的视图。
2. allocation 复用 In-Place Pod Resize 的路径；一次请求里的增删是原子生效。
3. 安全边界默认收紧：`pods/dynamic` 默认 RBAC 不授权，admission 按
   fail-closed 处理。
4. 这项能力在 1.37 没过 enhancements freeze；目前讨论目标转向 v1.38。

## 1. KEP 做了什么

### 1.1 核心机制

Dynamic Containers 允许在 Pod 已经 `Running` 后增删主容器。

这里的“动态”不是新增一个容器类型，也不是绕过 apiserver。它是把
`.spec.containers` 的可变更入口放到新 subresource `pods/dynamic`。

KEP 目标很集中：

- 把 Pod 创建/调度/初始化与 workload 执行解耦
- 支持高频增删容器
- 服务 warm pool、节点内二级调度（L2）这类低延迟场景

KEP 同时写了非目标：

- 不改 Pod 创建路径
- 不引入绕过 kube-apiserver 的旁路 mutation
- 不在本阶段做动态卷管理
- 不在本阶段做 running Pod 上的 mutable ResourceClaim
- 不新增 Pod phase/state

### 1.2 为什么现在提

面向对象主要是 AI/HPC 的延迟敏感 workload，不是通用微服务。

典型做法是先把这些重步骤完成：调度、`RunPodSandbox`、CNI、卷挂载、
设备初始化、InitContainer。之后再把短生命周期容器注入到已预热的 Pod。

官方 user story 包括：

- Ray/Slurm 这类框架在节点内做二级调度
- Agent warm pool
- restore/migration 快路径
- sidecar/daemon 原地替换

### 1.3 API 与权限边界

草案不加新顶层字段，主要变化在两个 subresource：

1. **`pods/dynamic`**（读写入口）
   - 在已有可变更范围外，允许增删 `.spec.containers`
   - 一次请求可同时新增和删除多个容器
2. **`pods/allocated`**（只读视图）
   - 展示 kubelet 侧 allocation 成功后的规格
   - 不在 apiserver/etcd 额外持久化一份新对象

`pods/dynamic` 不进入默认 `edit` ClusterRole，需要 cluster-admin
显式授权。

与 In-Place Resize 一样，desired spec 与 allocated spec 可能短时或长时不一致。
`pods/allocated` 的作用就是把“当前已分配状态”明确暴露出来。

### 1.4 增删容器的执行路径

新增容器的 allocation 与 In-Place Pod Resize 走同一套分配逻辑。
给新容器配置资源，本质上仍是 resize/allocate 问题，所以会出现
`Deferred` 或 `Infeasible`。

语义上有两点要抓住：

- 一次 `/dynamic` 请求中的增删改是**原子**的：全部可分配才提交
- allocation checkpoint 记录完整容器规格，kubelet 按 checkpoint 驱动后续 sync

状态变化（Alpha 草案）大致是：

- 容器已加入 spec 但未分配：`ContainerStatus=Waiting`，`reason=Unallocated`
- 分配成功：下次 pod sync 时由 allocation 更新，kubelet 拉起新容器
- 容器从 allocation 中删除但进程仍在跑：保持 `Running`，之后按
  `killContainer` 与 grace period 退出
- 已移除容器状态会暂存，再按现有 GC 机制清理

镜像更新也会被纳入同一次原子 allocation。也就是说，当分配还在
`Deferred` 时，镜像更新不会先单独落地。

### 1.5 Alpha 限制与安全默认值

当前 Alpha 限制包括：

- 只支持 main container，不能改 init container
- Pod 必须已 `Running` 且 init 全部完成
- 不支持通用 container mutation（同名容器需先完整移除再新增）
- 不改变 Pod QoS
- 新容器只能使用 Pod 里已存在的 volume/ResourceClaim
- 能力受 in-place resize 约束（如 Windows、启用 swap 的 Pod 不支持）
- 不能新增 privileged 容器
- 新容器不能使用 HostPort
- `.spec.containers` 至少保留一个 main container
- Pod 进入 terminating 后不再做 allocation

admission 策略是 **fail-closed**：

- 若某 webhook/policy 会拦截 `pods` 的 CREATE/UPDATE
- 但没有覆盖 `pods/dynamic`
- 则 `/dynamic` 请求直接拒绝

这条规则的目标很直接：避免旧策略因为新入口出现绕过。

## 2. 主要影响

### 2.1 生态默认假设会变化

过去生态里有个常见假设：主容器集合在 Pod 创建后不变。

Dynamic Containers 改的是这个集合本身，不只是镜像或资源字段。
因此依赖“只看 CREATE 事件”的 controller、注入器、监控索引、
按容器名聚合指标的组件，都需要检查 UPDATE 路径是否健壮。

草案当前的风险控制手段是：

- feature gate `DynamicContainers` 默认不打开
- 变更入口限制在 `pods/dynamic`
- `pods/dynamic` 默认 RBAC 不授权
- admission fail-closed

### 2.2 调度分层会更清晰

这项能力强化了一个实践模型：

```text
L1: kube-scheduler / PodGroup     负责放置、配额、隔离边界
L2: Ray/Slurm/Agent runtime       在节点内增删容器、细粒度调度
```

重点不是让 Kubernetes 放弃控制面，而是避免“每次短任务都创建新 Pod
并再次走完整初始化链路”。

### 2.3 安全边界从“主资源 UPDATE”转到“专用 subresource”

1.37 讨论里，一个关键转向是从“直接扩展 Pod UPDATE”改为“新建
`pods/dynamic`”。

这个转向配合默认不授权和 fail-closed，目的是把影响面收敛到显式启用的集群，
而不是一次性改变所有现有 Pod UPDATE 行为。

需要强调状态：创建时 dynamic opt-in 字段在当前草案里仍未定稿，
`@deads2k` 在 2026-09 的 review 里仍在追问。该点属于开放设计问题。

### 2.4 性能与可扩展性影响

KEP 提到的实际压力点包括：

- 短生命周期容器会放大 status PATCH 频率
- HPA/VPA 按容器名取指标时，目标容器可能动态消失
- Autoscaler 关注聚合资源，理论上应与 in-place resize 行为对齐

Alpha 性能目标写的是：在资源足够且不计拉镜像时，动态加容器到
`Running` 的额外开销 `< 500ms`。这与“端到端 sub-100ms 交互目标”
不是同一个指标。

## 3. 准备工作与 1.37 讨论时间线

### 3.1 这不是临时起意

Issue [#5972](https://github.com/kubernetes/enhancements/issues/5972)
在 **2026-03-23** 打开。相关背景能力包括：

- [KEP-1287 In-Place Pod Resize][ippr-ga]（1.35 GA）
- [KEP-2837 Pod-level resources](https://github.com/kubernetes/enhancements/issues/2837)
- [KEP-5474 Writable cgroups](https://kep.k8s.io/5474)
- [DRA CPU driver](https://github.com/kubernetes-sigs/dra-driver-cpu)

这些能力共同支持“先分配资源与运行边界，再在边界内调整执行体”。

公开里程碑如下：

| 日期 | 事件 |
| --- | --- |
| 2026-03-23 | Issue [#5972](https://github.com/kubernetes/enhancements/issues/5972) 打开，标题仍是 Optimistic Execution |
| 2026-04-30 | 设计文档进入 SIG Node 评审 |
| 2026-06-07 / 06-08 | `kep.yaml` 创建；[PR #6169](https://github.com/kubernetes/enhancements/pull/6169) 提交 |
| 2026-06-09 | PRR freeze 通过问卷，但仍是 *At risk for enhancements freeze* |
| 2026-06-12 | Tim Allclair 发起 SIG Architecture 邮件讨论 |
| 2026-06-13 | 出现 admission 边界与评审节奏争议 |
| 2026-06-15 | 设计转向 `pods/dynamic`，默认 `edit` 不授权 |
| 2026-06-16 | `@enj` 与 `@deads2k` 在 PR `/hold` |
| 2026-06-16 AoE / 06-17 UTC | 1.37 enhancements freeze |
| 2026-06-17 | Enhancements 团队确认未达标；后续讨论引入 fail-closed |
| 2026-09-08 | `@haircommander` `/milestone v1.38`，重新 lead-opted-in |

### 3.2 1.37 讨论的核心分歧

讨论主要发生在两处：

- **6 月 12–13 日**：SIG Architecture 邮件列表线程
- **6 月 15–17 日**：KEP PR 上关于 `/dynamic`、`/hold`、freeze 的讨论

争议重点不是“方向是否有价值”，而是“是否给了足够的跨 SIG 评审窗口”。

- 支持侧：Alpha 默认关闭，先进入周期拿真实反馈
- 反对侧：改动触及长期 API/生态假设，评审窗口不应压缩到几天

随后设计继续收敛：

- 写入独立 subresource `pods/dynamic`
- 默认 RBAC 不授权
- SIG Auth 讨论补上 fail-closed

最终结果是：**1.37 未进入，继续评审并转向 v1.38 节奏**。

### 3.3 设计收敛后，代码铺垫已开始

在 #6169 讨论期，已有配套 PR：

- [`kubernetes/kubernetes#140659`](https://github.com/kubernetes/kubernetes/pull/140659)：
  Pod `/allocated` subresource
- [`kubernetes/kubernetes#140856`](https://github.com/kubernetes/kubernetes/pull/140856)：
  kubelet `/allocatedPods`
- [`kubernetes/kubernetes#141039`](https://github.com/kubernetes/kubernetes/pull/141039)：
  allocation checkpoint 记录完整 PodSpec

这些实现方向与 KEP 一致：默认 gate 关闭时不改变现有 Pod 行为；
只有显式走 `/dynamic` 的请求才触发新语义。

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
