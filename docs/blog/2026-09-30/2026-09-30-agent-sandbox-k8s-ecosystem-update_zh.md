---
status: Active
maintainer: pacoxu
date: 2026-09-30
last_updated: 2026-09-30
tags: kubernetes, agent-sandbox, agent-substrate, google-ax, gvisor, kata, openshell, azure, opensandbox, cubesandbox, kep-5972, ai-infrastructure
canonical_path: docs/blog/2026-09-30/2026-09-30-agent-sandbox-k8s-ecosystem-update_zh.md
source_urls:
  - https://github.com/pacoxu/AI-Infra/blob/main/docs/archive-blog/2025-11-28/2025-11-28-agent-sandbox_zh.md
  - https://github.com/kubernetes-sigs/agent-sandbox
  - https://github.com/kubernetes-sigs/agent-sandbox/releases/tag/v1.0.0
  - https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/
  - https://github.com/agent-substrate/substrate
  - https://github.com/google/ax
  - https://cloud.google.com/blog/products/containers-kubernetes/agent-substrate-available-on-gke
  - https://gvisor.dev
  - https://github.com/NVIDIA/OpenShell
  - https://learn.microsoft.com/en-us/azure/container-apps/sandboxes-overview
  - https://azure.microsoft.com/en-us/blog/designing-agent-first-platforms-what-changes-when-agents-do-the-work/
  - https://katacontainers.io/blog/kata-containers-openinfra-summit-asia-2026-schedule/
  - https://katacontainers.io/blog/kata-containers-agent-sandbox-integration/
  - https://github.com/alibaba/OpenSandbox
  - https://github.com/TencentCloud/CubeSandbox
  - https://www.volcengine.com/docs/6460/144953
  - https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5972-dynamic-containers/README.md
  - https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5972-dynamic-containers/kep.yaml
---

# Agent 沙盒十个月：从 agent-sandbox 1.0 到 Dynamic Containers

> 续写：[Agent Sandbox：在 Kubernetes 上安全运行 AI 代理](../../archive-blog/2025-11-28/2025-11-28-agent-sandbox_zh.md)
> （2025-11-28）。

十个月前，社区在讲「Kubernetes 终于有了面向 Agent 的 Sandbox CRD」。今天更值得记的是：
上游 **agent-sandbox 进入 1.0**；云厂商把「高密度 + 隔离」做成可部署栈；国内云与
Kata 社区在同一问题上给出不同解法；而 Kubernetes 本体则用
[KEP-5972 Dynamic Containers](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5972-dynamic-containers/README.md)
开始改写「Pod 容器列表创建后不可变」这条十年假设。

## 一、agent-sandbox 1.0：里程碑为什么重要

[kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)
于 **2026-08-28** 发布
[v1.0.0](https://github.com/kubernetes-sigs/agent-sandbox/releases/tag/v1.0.0)
（当前补丁到 [v1.0.4](https://github.com/kubernetes-sigs/agent-sandbox/releases/tag/v1.0.4)）。
对 SIG Apps 下这个年轻项目来说，1.0 不是「功能清单变长」，而是 **API 契约稳定下来**：

1. **API 收敛到 `v1beta1`，砍掉 `v1alpha1` 与 conversion webhook**  
   读写路径少一层转换，informer 同步不再为旧版本付 CPU；也少了 webhook 证书、私有
   集群防火墙一类故障面。从实验对象变成可被 GitOps / OLM 长期跟的控制器。
2. **声明式生命周期成为公约**  
   `Sandbox` / `SandboxTemplate` / `SandboxClaim` / `SandboxWarmPool` 这套面，把
   「有状态单例 + 预热认领」从各家私有实现里抽出来。3 月官方博客
   [Running Agents on Kubernetes with Agent Sandbox](https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/)
   已把它写成上游叙事。
3. **隔离仍可插拔**  
   项目明确自己是 *sandbox orchestrator*：强隔离交给 `RuntimeClass` 后端（gVisor、
   Kata / Firecracker 等），不和某一家 hypervisor 绑死。
4. **SDK、路由、RL 入口成型**  
   `sandboxd`、sandbox-router 的浏览器 path routing、NeMo Gym / Gymnasium 集成，说明
   消费方已经从「演示 CRD」走到 coding agent、评测与训练回路。

**为什么说这是里程碑：** Agent 执行环境终于有了一层可移植的 Kubernetes 原语。之上可以
叠云厂商的高密度运行时，之下可以换隔离后端；左右还可以对接 RL / harness。没有这层
公约，后面各家的 Substrate、Cube、OpenSandbox 都会被迫各自发明一套「认领预热沙盒」
的 API。

后续 1.0.x 主要在补生产细节：lifecycle Events、WarmPool 竞态、RL run isolation、
MCP / 多语言 SDK。方向没变，是把 1.0 的契约跑稳。

## 二、GKE 实践栈，以及海外商业方案

开源公约之外，真正把「百万级空闲 Agent」跑起来的，往往是 **控制面 + 执行层 + 隔离
后端** 的组合。Google 在 GKE 上把这条链公开得最完整。

### GKE：Agent Substrate + AX + gVisor / microVM

| 层 | 项目 | 做什么 |
| --- | --- | --- |
| 任务编排 | [google/ax](https://github.com/google/ax)（Agent Executor） | 用 `Task` / `Workspace` / `Model` 声明式跑 agent 任务；`ax apply` / `ssh` / `suspend` |
| 高密度执行 | [agent-substrate/substrate](https://github.com/agent-substrate/substrate) | Actor ↔ Worker 多路复用；suspend/resume；把空闲态从算力账单里抠掉 |
| 机器与隔离 | GKE + [gVisor](https://gvisor.dev) / Cloud Hypervisor | K8s 管 Worker；sandbox 默认安全隔离与网络边界 |

要点可以压缩成三句：

- **Agent Substrate** 承认 Agent 大部分时间在等模型或人：大量 Actor 复用少量 Worker，
  宣称 resume < 500ms、每秒数百次激活、单机可压上千 dormant agents。GKE 上已有产品化
  叙事（本仓另有
  [中文摘译](../2026-09-16/2026-09-16-agent-substrate-available-on-gke_zh.md)）。
- **AX** 是 Substrate 之上的 harness 运行时：生产推荐跑在 Substrate 上；CLI 刻意做成
  `kubectl` 形状，方便平台团队 GitOps。
- **gVisor**（以及 microVM）仍是「不可信代码默认落点」。GKE Agent Sandbox add-on
  本身也建立在上游 agent-sandbox 之上，和 Substrate 形成「公约 CRD + 密度层」的双轨。

这条栈回答的是：**如何在 Kubernetes 上既保留可移植性，又把密度和安全做成可运维产品。**

### 海外商业 / 平台方案（对照）

同一问题，云厂商并不都走「开源 CRD + 自托管」：

**NVIDIA OpenShell**  
[NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell) 偏 **策略执行层**：内核侧约束
文件、系统调用与网络；凭证不进沙盒明文，只在打向批准 endpoint 时注入；策略变更可做
形式化检查。支持本地与 Kubernetes Helm。它和 agent-sandbox / Substrate 是互补关系——
后者管生命周期与密度，前者管「跑起来之后允许碰什么」。

**Microsoft Azure Container Apps Sandboxes**  
Azure 把沙盒做成一等资源（`Microsoft.App/SandboxGroups`），硬件隔离 microVM，自带
suspend/resume、预热池与 egress 策略；公开材料称微软内部日均百万级沙盒，承接 GitHub
Copilot、Foundry Hosted Agents 等。路径是 **平台原语**，不是「在 AKS 上装一个 CRD」；
和 Dynamic Sessions（短时 code interpreter）刻意分开。对标时要分清：托管执行底座 vs
自建 K8s 控制面。

海外还有 E2B 等托管 code-execution 服务，SDK 接口常被后来者兼容。整体趋势一致：
**隔离 + 亚秒启停 + 空闲不计费 + 凭证不出沙盒。**

## 三、国内现场：Kata 社区与云厂商沙箱

KubeCon + CloudNativeCon + OpenInfra Summit China 把「Agent 需要什么底座」推到了明面。
Kata 社区的叙事很清楚：从云原生安全容器，走到 **Agent 时代的默认强隔离后端**。

### Kata：会上看到的实践信号

- 蚂蚁等团队分享用 **Kubernetes Agent Sandbox 做生命周期 + Kata 做 guest 内核边界**
  的 Agent Runtime（开源基础设施拼装，而不是另起一套私有编排）。
- Kata 路线图强调 4.0：Rust runtime、多 hypervisor、模板化启动（亚 100ms 量级）、
  Confidential Computing，以及面向 AI agent / 安全沙箱的能力扩展。
- 与上游的正式协作早有铺垫：
  [Kata ↔ Agent Sandbox 集成博客](https://katacontainers.io/blog/kata-containers-agent-sandbox-integration/)；
  agent-sandbox 文档也给出
  [Kata + Firecracker（`kata-fc`）](https://agent-sandbox.sigs.k8s.io/docs/use-cases/examples/firecracker-sandbox/)
  示例（约 125ms 启动）。

国内会上反复出现的组合是：**社区公约管认领与身份，Kata（或同类 microVM）管隔离强度。**

### 国内云厂商：字节 / 火山、腾讯、阿里

公开材料里，三家都已经走出「只有内部沙箱」的阶段，但切入点不同：

**字节 / 火山引擎**  
[VCI Agent Sandbox](https://www.volcengine.com/docs/6460/144953) 走弹性容器实例
（VCI）与云原生沙箱服务；公开描述强调基于社区 Agent Sandbox 深度开发，并用 Kata
做强隔离，覆盖 AgentServing、AgentRL 等。AgentKit 一侧则提供 AIO / 代码 / 浏览器等
沙箱模板，偏「Agent 平台开箱即用」。

**腾讯云 CubeSandbox**  
[TencentCloud/CubeSandbox](https://github.com/TencentCloud/CubeSandbox)（约 2026-04
开源）用 RustVMM + **Cloud Hypervisor**（而非 Firecracker）做 microVM，主打亚百毫秒
启动与低内存开销，并强调 E2B SDK 兼容。背景是 Serverless 沙箱能力延伸到 Agent；开源
动机之一，是 Agent 迭代快于基础设施共识，需要开放底座让生态一起试。

**阿里 OpenSandbox**  
[alibaba/OpenSandbox](https://github.com/alibaba/OpenSandbox) 走 **协议 + 可插拔
runtime**：Docker / gVisor / Kata / Firecracker 可换；统一沙箱 API、多语言 SDK、MCP；
Fast Sandbox 路径上公开了 Firecracker 预热与 pause/resume 数字。更像「企业要把沙箱
嵌进已有 K8s」时的抽象层，而不是绑死一家 hypervisor。

粗看对照：

| | 火山 VCI Agent Sandbox | 腾讯 CubeSandbox | 阿里 OpenSandbox |
| --- | --- | --- | --- |
| 与社区关系 | 基于 agent-sandbox 深化 | 自研 microVM 栈 + E2B 兼容 | 统一 API + 多 runtime |
| 隔离 | Kata 等 | Cloud Hypervisor microVM | runc → gVisor → Kata/FC |
| 形态 | 云产品 + K8s 语义 | 开源底座 / 可自托管 | 开源平台 + K8s operator |

国内版图和海外一样在分层，只是产品包装不同：**有人押社区 CRD，有人押自研 VMM，有人
押协议可插拔。** 共同压力仍是突发创建、有状态、强隔离、空闲成本。

## 四、回到 Kubernetes：KEP-5972 Dynamic Containers

沙箱项目再热闹，最终还是要落在 Pod 模型上。十年假设之一是：`.spec.containers` 在
CREATE 之后基本是闭集（ephemeral containers 只是调试旁路）。Agent / Ray / 训练框架
却需要在 **同一资源信封里** 频繁增减主容器、换工具镜像、做 warm-pool 热切换——今天
往往只能「另起一个 Pod」或「绕开 API」。

[KEP-5972: Dynamic Containers](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5972-dynamic-containers/README.md)
已经合入 enhancements，[`kep.yaml`](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5972-dynamic-containers/kep.yaml)
标明 **stage: alpha，目标里程碑 v1.38**，feature gate `DynamicContainers`。

它打破的预设包括：

- 主容器列表不再只能在创建时定死；通过显式子资源 `pods/dynamic` 增删 main container  
- 默认 `edit` 角色 **不授予** `/dynamic`；admission fail-closed——可变性不是「随便
  UPDATE Pod」  
- allocation 与 In-Place Pod Resize 协同；KEP 正文直接写了
  **Warm-pools for agentic workloads**、以及和 Ray / Slurm 一类框架的分层调度故事  

对 Agent 时代，这意味着：L1（调度 / 配额 / 节点放置）可以继续由 Kubernetes 守住；
L2（沙箱内容器 churn、工具进程、短生命周期执行器）有机会合法地发生在同一个 Pod
信封里。agent-sandbox 的 WarmPool、Substrate 的 Actor/Worker、OpenSandbox 的 Fast
Sandbox、Cube 的微秒级启停——都可能在下一阶段与这条 API **共同进化（co-evolution）**，
而不是永远在控制器外各自打补丁。

1.38 alpha 仍是谨慎试验：策略、可观测性、第三方假定「容器静态」的控制器都要跟着改。
但方向已经写进上游——这和 agent-sandbox 1.0 一样，是 **公约层** 的进展。

## 结语

从 2025 年底的「有一个 Sandbox CRD」，到 2026 秋天，可以记住四件事：

1. **agent-sandbox 1.0** 让生命周期公约可跟、可迁移、可被云产品承接。  
2. **GKE 栈（Substrate + AX + gVisor/microVM）** 示范了高密度生产路径；NVIDIA /
   Azure 则分别补强策略层与托管原语。  
3. **国内** 在 KubeCon / OpenInfra 现场看到 Kata 与 Agent Sandbox 的合流；火山、腾讯、
   阿里各自用社区深化、自研 VMM、协议可插拔三种姿态入场。  
4. **KEP-5972** 在 1.38 以 alpha 挑战 Pod 不可变容器列表——给 Agent 沙箱与编排层留出
   与 Kubernetes 本体一起演进的接口。

接下来真正有意思的，不是再冒出一个沙箱品牌，而是这些层能否在 **同一套上游假设**
上收敛：声明式认领、可插拔隔离、空闲可挂起、策略出进程，以及——动态容器落地后的
共同进化。

---

*整理自各项目发行说明、官方文档、KubeCon / OpenInfra 公开议程与 KEP 正文。版本与
产品能力仍在快速变化，落地上以对应仓库与云文档为准。*
