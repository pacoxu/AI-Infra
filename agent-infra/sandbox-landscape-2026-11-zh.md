---
status: Active
maintainer: pacoxu
date: 2026-11-17
last_updated: 2026-11-17
tags: agent-sandbox, agent-substrate, kagent, google-ax, opensandbox, openkruise, cubesandbox, e2b, microsandbox, sandbox-runtime, nvx, ai-infrastructure
canonical_path: agent-infra/sandbox-landscape-2026-11-zh.md
source_urls:
  - https://github.com/kubernetes-sigs/agent-sandbox
  - https://github.com/opensandbox-group/OpenSandbox
  - https://github.com/openkruise/agents
  - https://github.com/agent-substrate/substrate
  - https://opensource.googleblog.com/2026/11/sandboxing-untrusted-ai-agents-at-scale.html
  - https://github.com/kagent-dev/kagent
  - https://github.com/google/ax
  - https://github.com/TencentCloud/CubeSandbox
  - https://github.com/e2b-dev/E2B
  - https://github.com/e2b-dev/runtime
  - https://github.com/superradcompany/microsandbox
  - https://github.com/anthropics/sandbox-runtime
  - https://github.com/microsoft/nvx
---

# Agent 沙箱项目全景（2026-11）

> **注意：** 本文部分内容由 AI（Claude）辅助整理。版本号和 star 数取自 2026-11-17 的 GitHub 仓库，
> 启动、恢复耗时均为项目自报。使用前请对照上游仓库核实。

社区里常把 Agent 沙箱项目分成两条路线。
「K8s 托管派」用 CRD 和 Pod 承载沙箱，「自建调度派」自己做调度和 microVM 池。
这个划分好记，但会把不同层的项目放进同一列。
本文先按层归位，再逐个介绍，最后核对两路线划分里不准的地方。

策略与数据面（OpenKruise Agents v0.6.0、MXC、Strands Box、ACK）见
[Agent 沙箱控制面（2026-10）](./sandbox-control-planes-zh.md)。

## 先分层

| 层 | 项目 | 回答的问题 |
| --- | --- | --- |
| Agent 编排 | kagent 1.x、Google AX | Agent 或 Task 怎么声明，交给谁执行 |
| 沙箱原语 / 服务 | Pod 即沙箱：Agent Sandbox、OpenSandbox、OpenKruise Agents；Pod 即 Worker：Agent Substrate；自有调度：E2B、CubeSandbox | 沙箱的生命周期、调度、挂起与恢复 |
| 隔离运行时 / 库 | microsandbox、NVX；底层 gVisor、Kata、Firecracker、Cloud Hypervisor | 不可信代码和宿主之间的内核或硬件边界 |
| 进程约束 | sandbox-runtime；同类思路还有 agent-sandbox 仓库里的 nono 示例（Landlock / Seatbelt） | 一个进程能读写哪些路径、连哪些域名 |

一个平台通常每层各选一个。同层项目才互相替代，跨层项目是叠加关系。

## 总表

| 项目 | 层 | 与 K8s 的关系 | 隔离边界 | 挂起 / 快照 | 版本（2026-11-17） | Star |
| --- | --- | --- | --- | --- | --- | --- |
| [Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox) | 沙箱原语 | `Sandbox` = 一个有状态 Pod；CRD + 控制器 | 由 RuntimeClass 决定：gVisor、Kata（QEMU / Firecracker）、urunc、AWS Nitro 等 | 自身不做内存快照；GKE 上可配 Pod Snapshot（有示例） | v1.0.11（11-12） | 4.6K |
| [OpenSandbox](https://github.com/opensandbox-group/OpenSandbox) | 沙箱服务 | K8s provider 为自家 `BatchSandbox`（默认）或 SIG agent-sandbox；也可只用 Docker | RuntimeClass：gVisor / Kata / Firecracker | Firecracker 沙箱可带内存和磁盘暂停恢复；BatchSandbox 用 rootfs 快照镜像 | release-1.3.0-rc.1（11-16） | 17.5K |
| [OpenKruise Agents](https://github.com/openkruise/agents) | 沙箱原语 + 数据面 | `agents.kruise.io` CRD，另有 E2B 兼容 API | RuntimeClass | 探针驱动的自动暂停恢复；`CheckpointRestore` 保留 rootfs 可写层 | v0.6.0（10-07） | — |
| [Agent Substrate](https://github.com/agent-substrate/substrate) | Actor 运行时 | `WorkerPool`、`SandboxConfig` 是 CRD；actor 状态在自有控制面 + PostgreSQL | 每个运行中的 actor 一个 gVisor（默认）或 Kata + Cloud Hypervisor microVM，按 WorkerPool 选 | 进程级内存快照，恢复 < 500 ms | v1.0.0（11-05） | 7.4K |
| [kagent](https://github.com/kagent-dev/kagent) | Agent 编排 | `Agent`、`Harness` 等是 CRD；执行交给 Substrate | 继承 Substrate | 由 Substrate 负责 | v1.0.1（11-12） | 4.4K |
| [Google AX](https://github.com/google/ax) | Agent 编排 | `Task` 跑成 Substrate actor；自有 `ax-server` + PostgreSQL；`ax.io/v1alpha1` 由 `ax` CLI 下发，不是 CRD | 继承 Substrate | 继承 Substrate 的亚秒挂起恢复 | v0.3.1（09-25） | 14.8K |
| [CubeSandbox](https://github.com/TencentCloud/CubeSandbox) | 沙箱服务 | 自有调度 CubeMaster；v0.6 起可部署到 K8s（预览） | 每沙箱一个 KVM microVM（RustVMM） | CubeCoW 快照、克隆、回滚；自动暂停恢复；跨节点恢复（预览） | v0.8.0（11-12） | 13.3K |
| [E2B](https://github.com/e2b-dev/E2B) | 沙箱服务（云 + 自托管） | 自有 API 和每节点 orchestrator；可用 Terraform、K8s 清单或单机 Embed 部署 | 每沙箱一个 Firecracker microVM | 沙箱 = 从模板快照恢复；暂停把内存和磁盘差异写入对象存储；可 fork | SDK 2.64.0（11-13） | 14.9K |
| [microsandbox](https://github.com/superradcompany/microsandbox) | 可嵌入 microVM 库 | 无，本机运行 | libkrun microVM：Linux KVM、macOS Apple Silicon、Windows WHP | fork、snapshot、restore | v0.7.15（11-12） | 9.1K |
| [NVX](https://github.com/microsoft/nvx) | 可嵌入 microVM（研究原型） | 无，也没有 CRI 集成 | OpenVMM microVM（Linux guest）；KVM / MSHV / WHP | README 未提 | v0.1.0-dev（预发布） | 849 |
| [sandbox-runtime](https://github.com/anthropics/sandbox-runtime) | 进程级沙箱 | 无 | 不用容器或 VM：Seatbelt、bubblewrap + seccomp、Windows（alpha） | 无 | v0.0.83（11-13） | 7.2K |

## 项目介绍

### Kubernetes SIG Agent Sandbox

[kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)，SIG Apps 子项目。

- 一个 `Sandbox` 对应一个有状态 Pod，配套 `SandboxTemplate`、`SandboxClaim`、`SandboxWarmPool`。
- 隔离强度由 RuntimeClass 决定。
  仓库示例覆盖 gVisor、Kata（QEMU / Firecracker）、urunc、AWS Nitro（`isolated-sandbox` RuntimeClass）、
  Pod 内 Hyperlight、容器内 QEMU 跑 Windows、docker-sbx、nono。
- 自身不做内存快照；GKE 上可以配 Pod Snapshot，仓库里有示例。
- KubeVirt 目前只有提案（[#1157](https://github.com/kubernetes-sigs/agent-sandbox/issues/1157)、
  [#1650](https://github.com/kubernetes-sigs/agent-sandbox/issues/1650)），没有合入的集成。

### OpenSandbox

[opensandbox-group/OpenSandbox](https://github.com/opensandbox-group/OpenSandbox)，原 `alibaba/OpenSandbox`。

- 面向 Agent 的沙箱服务，提供多语言 SDK、`osb` CLI 和 MCP。
- 运行时可以是 Docker，也可以是 Kubernetes。
  K8s 上有两种 provider：自家 `BatchSandbox`（配 Pool，默认）和 SIG agent-sandbox。
- 隔离走 RuntimeClass：gVisor、Kata、Firecracker。
  Firecracker 沙箱支持带内存和磁盘的暂停恢复；BatchSandbox 用 rootfs 快照镜像。
- 项目自报 Firecracker 沙箱创建耗时 P50 64 ms、P99 125.4 ms（10 并发）。

### OpenKruise Agents

[openkruise/agents](https://github.com/openkruise/agents)，OpenKruise（CNCF 孵化项目）的子项目。

- `agents.kruise.io` CRD 加 E2B 兼容 API，同一批沙箱有两种入口。
- v0.6.0 带来集群内数据面：Pod 内 L4 拒绝、网关 L7 与 MCP ACL、凭证注入、`PoolAutoscaler`、探针驱动的暂停恢复。
- 详见 [Agent 沙箱控制面（2026-10）](./sandbox-control-planes-zh.md)。

### Agent Substrate

[agent-substrate/substrate](https://github.com/agent-substrate/substrate)，CNCF Sandbox 项目。
Google 在 2026-11-05 宣布把 Agent Substrate、gVisor 和 OpenRL 捐给 CNCF，同时发布 Substrate 1.0。

- 把大量有状态 actor 复用到少量就绪的 Worker Pod 上，K8s 控制面不在热路径里。
- `WorkerPool`、`SandboxConfig` 是 CRD。
  actor 本身的状态在 Substrate 自有控制面（`ate`）和 PostgreSQL 里，不是 K8s 对象。
- 每个运行中的 actor 有独立沙箱：默认 gVisor，也可以是 Kata + Cloud Hypervisor microVM，按 WorkerPool 选。
  actor 以子 cgroup 的形式运行在 Worker Pod 里。
- 挂起时做进程级内存快照。README 和 Google 博客给的恢复耗时都是 500 ms 以内。
- kagent 1.x 和 Google AX 都跑在它上面。

### kagent

[kagent-dev/kagent](https://github.com/kagent-dev/kagent)，CNCF Sandbox 项目（2025-05-22 接收）。

- `Agent`、`Harness` 等仍是 CRD，支持 A2A、MCP、gRPC。
- 1.x 把执行交给 Substrate（controller → Substrate → agent runtime），挂起、恢复和快照都由 Substrate 负责。

### Google AX

[google/ax](https://github.com/google/ax)。仍是 0.x，稳定版之前可能有破坏性变更。

- 需要装好 Agent Substrate 的 Kubernetes 1.36+。
- 四个原语：`Task`、`Workspace`、`Gateway`、`Model`。
  每个 `Task` 是一个 Substrate actor，挂起恢复能力来自 Substrate。
- `ax install` 部署 `ax-server` 和 PostgreSQL。
  清单是 `ax.io/v1alpha1`，由 `ax` CLI 下发，不是 K8s CRD。

### CubeSandbox

[TencentCloud/CubeSandbox](https://github.com/TencentCloud/CubeSandbox)，腾讯云开源。

- 自有调度 CubeMaster，每个沙箱一个 KVM microVM（RustVMM）。
- 项目自报冷启动 60 ms 以内，单实例开销 5 MB 以内。
- CubeCoW 快照、克隆、回滚，自动暂停恢复，跨节点恢复（预览）。
- 兼容 E2B SDK，改一个环境变量即可切换。
  v0.6 起控制面和计算节点可以部署到 K8s 上（预览），但调度仍在 CubeMaster。

### E2B

[e2b-dev/E2B](https://github.com/e2b-dev/E2B)（SDK）和 [e2b-dev/runtime](https://github.com/e2b-dev/runtime)（运行时与自托管）。

- 每个沙箱一个 Firecracker microVM。
  沙箱从模板快照恢复而来；暂停时把内存和磁盘差异写入对象存储；支持 fork。
- 自有 API 和每节点 orchestrator，不依赖 K8s 调度。
  自托管可以用 Terraform（GCP、AWS、Azure）、K8s 清单，或单机 Embed。
- E2B API 已经是事实上的协议：CubeSandbox 和 OpenKruise Agents 都提供兼容接口。

### microsandbox

[superradcompany/microsandbox](https://github.com/superradcompany/microsandbox)，原 zerocore-ai。

- 基于 libkrun 的可嵌入 microVM，支持 Linux KVM、macOS Apple Silicon、Windows WHP。
- 直接用 OCI 镜像，项目自报启动 100 ms 以内；支持 fork、snapshot、restore。
- 提供嵌入式 SDK、`msb` CLI 和 MCP。没有 K8s 集成，定位是本机或自建平台的积木。

### Anthropic sandbox-runtime

[anthropics/sandbox-runtime](https://github.com/anthropics/sandbox-runtime)（`srt`），Beta research preview。

- 不用容器或 VM，直接用操作系统机制：macOS Seatbelt，Linux bubblewrap + seccomp，Windows（alpha）用独立账号 + WFP。
- 文件系统读默认放行、写默认拒绝。
  网络默认拒绝，经宿主上的 HTTP / SOCKS5 代理按域名白名单放行，可选凭证遮蔽。
- 为 Claude Code 开发，也可以包住 MCP server。
- 共享宿主内核，是能力围栏，不是硬件边界。适合叠在容器或 microVM 里面用，不替代它们。

### Microsoft NVX

[microsoft/nvx](https://github.com/microsoft/nvx)，MIT 许可，2026-08 创建，目前只有 v0.1.0-dev 预发布。

- 来自 MSR Systems Research 和 Azure Research – Systems，基于 Nanvix 研究。
- 用 OpenVMM 起 Linux guest microVM：Linux 上走 KVM 或 MSHV，Windows 上走 WHP。提供 `nvx` CLI 和 Rust 库。
- 和 microsandbox 同层。暂无 K8s / CRI 集成，也没有公开的启动数据。

## 核对两路线划分

| 常见说法 | 核对结果 |
| --- | --- |
| Google AX 属于 K8s 托管派 | 不准确。AX 跑在 Substrate 上，自带 server 和数据库，清单不是 CRD。它有四个原语，常被漏掉的是 `Gateway`。 |
| kagent 属于 K8s 托管派 | 只对一半。1.x 的 API 是 CRD，执行在 Substrate，横跨两条路线。 |
| OpenSandbox 通过 provider 接 SIG CRD | 只对一半。K8s 上默认用自家 `BatchSandbox`，SIG agent-sandbox 是可选 provider。 |
| CubeSandbox 完全脱离 K8s | 基本对。v0.6 起能部署到 K8s（预览），但 K8s 只是承载，调度仍在 CubeMaster。 |
| E2B 协议成为标准 | 有佐证。CubeSandbox 兼容 E2B SDK，OpenKruise Agents 同时提供 E2B API 和 K8s API。 |
| Agent Substrate 每个 actor 一个 gVisor 或 microVM | 对。默认 gVisor，可选 Kata + Cloud Hypervisor，按 WorkerPool 选。 |

sandbox-runtime 和 NVX 不属于任何一条路线：前者是进程约束层，后者是 microVM 积木层。

## 和 Dynamic Containers 的关系

Agent Substrate 把 Pod 当成 Worker，在 Pod 里用子 cgroup 放 actor，Kubernetes 只看到 Worker Pod。
KEP-5972 Dynamic Containers 想在 Kubernetes API 里补上相近的能力：通过 `pods/dynamic` 子资源给运行中的 Pod 增删主容器。
实现 PR 在 2026-11-12 至 11-14 陆续合入
（[#143364](https://github.com/kubernetes/kubernetes/pull/143364)、
[#143714](https://github.com/kubernetes/kubernetes/pull/143714)、
[#143715](https://github.com/kubernetes/kubernetes/pull/143715)），
目标 v1.38 Alpha，feature gate 默认关闭。
设计要点见 [Kubernetes Dynamic Containers Update](./README.md#kubernetes-dynamic-containers-update-2026-09-30)。

## 选型提示

1. 要中立的 K8s API、沙箱即 Pod：Agent Sandbox。还要集群内 L7、MCP ACL 和凭证注入：OpenKruise Agents。
2. 要现成的 SDK、CLI，并在 Docker 和 K8s 之间切换：OpenSandbox。
3. 大量空闲、需要亚秒唤醒的有状态 Agent：Agent Substrate。
   在它上面用 CRD 声明 Agent 选 kagent 1.x；需要 Task / Workspace / Gateway / Model 这套抽象再看 Google AX。
4. 要 E2B 兼容 API 的自托管 microVM 池：CubeSandbox 或自托管 E2B。
5. 开发机或单机嵌入 microVM：microsandbox。NVX 目前适合跟踪，不适合上生产。
6. 本地编码 Agent 的文件和网络围栏：sandbox-runtime。它可以和上面任何一层叠加。

## 参考

- <a href="https://github.com/kubernetes-sigs/agent-sandbox">`kubernetes-sigs/agent-sandbox`</a>：Kubernetes SIG Apps 子项目
- <a href="https://github.com/opensandbox-group/OpenSandbox">`opensandbox-group/OpenSandbox`</a>：原 `alibaba/OpenSandbox`
- <a href="https://github.com/openkruise/agents">`openkruise/agents`</a>：OpenKruise（CNCF 孵化项目）子项目
- <a href="https://github.com/agent-substrate/substrate">`agent-substrate/substrate`</a>：CNCF Sandbox
- <a href="https://opensource.googleblog.com/2026/11/sandboxing-untrusted-ai-agents-at-scale.html">Google Open Source
  Blog：Agent Substrate 与 gVisor 捐赠给 CNCF</a>（2026-11-05）
- <a href="https://github.com/kagent-dev/kagent">`kagent-dev/kagent`</a>：CNCF Sandbox
- <a href="https://github.com/google/ax">`google/ax`</a>：跑在 Agent Substrate 上的 Agent 平台
- <a href="https://github.com/TencentCloud/CubeSandbox">`TencentCloud/CubeSandbox`</a>：腾讯云开源
- <a href="https://github.com/e2b-dev/E2B">`e2b-dev/E2B`</a>、<a href="https://github.com/e2b-dev/runtime">`e2b-dev/runtime`</a>
- <a href="https://github.com/superradcompany/microsandbox">`superradcompany/microsandbox`</a>
- <a href="https://github.com/anthropics/sandbox-runtime">`anthropics/sandbox-runtime`</a>：Anthropic
- <a href="https://github.com/microsoft/nvx">`microsoft/nvx`</a>：Microsoft Research 研究原型
- [AI Agent Platforms and Frameworks](./README.md)：英文总览，含 2026-11 更新小节
