---
status: Active
maintainer: pacoxu
date: 2026-03-13
tags: kubernetes, nvidia, gpu, aicr, gitops, cluster-runtime
canonical_path: docs/blog/2026-03-13/nvidia-aicr-introduction_zh.md
source_urls:
  - https://github.com/NVIDIA/aicr
  - https://github.com/pacoxu/AI-Infra/pull/252
---

# NVIDIA AICR：把 GPU 集群安装经验固化成可复现 Recipe

2026 年 3 月 13 日，AI-Infra 仓库合并了
[PR #252](https://github.com/pacoxu/AI-Infra/pull/252)，把
**NVIDIA AI Cluster Runtime（AICR）** 加入了 landscape 和文档索引。
这个项目很新，但它切中的问题非常实际：**GPU Kubernetes 集群并不难“装起来”，难的是稳定、可验证、可复现地一次次装对。**

如果你做过 AI 平台、训练平台或者推理集群，大概率都踩过类似坑：

- 同样是 Ubuntu，内核小版本不同，结果驱动行为不一致；
- GPU Operator 能装上，但和 Network Operator、驱动版本、Kubernetes 版本组合起来并不稳定；
- 一套“能跑”的配置只存在于某位资深同事的 runbook 里，换个环境就要重试一遍；
- Helm values、集群基线和验收标准散落在多个仓库，难以做版本锁定和审计。

AICR 想解决的，就是这类“平台经验无法产品化”的问题。

## AICR 是什么？

AICR 可以理解为一个 **面向 GPU Kubernetes 集群的 recipe 生成与校验工具**。
它不是新的 Kubernetes 发行版，也不是云厂商托管服务，而是站在更高一层，
把一组已经验证过的组件组合固化成可重复使用的“配方”。

官方给出的关键词有三个：

- **Optimized**：针对特定硬件、云环境、OS 和工作负载做过调优；
- **Validated**：发布前经过自动化兼容性与约束检查；
- **Reproducible**：同样输入可以生成相同部署结果。

换句话说，AICR 不是替你“发明”最佳实践，而是把 NVIDIA 已知可行的 GPU 集群组合，
以机器可消费的方式交付出来。

## 它解决的核心问题是什么？

AI 基础设施和普通 Kubernetes 平台的一个关键差异是：**兼容性矩阵太复杂**。

你需要同时考虑：

- GPU 型号，例如 H100、GB200；
- 云环境，例如 EKS、GKE，或自建集群；
- OS 与内核版本；
- NVIDIA 驱动；
- GPU Operator、Network Operator 等平台组件；
- 上层工作负载意图，是训练还是推理；
- 部署方式，是 Helm、ArgoCD、Flux 还是自定义流水线。

这些变量单看都不新鲜，但真正麻烦的是它们的**组合爆炸**。AICR 的思路是：
不要让每个团队自己手工维护一份“最佳组合表”，而是直接发布一套经过验证的 recipe。

## AICR 的核心抽象：Recipe、Overlay、Bundle

这是理解 AICR 最重要的三个概念。

### 1. Recipe

Recipe 是一份**版本锁定的目标环境配置**。你告诉 AICR 目标环境，例如：

- 云平台：EKS / GKE / 自建；
- GPU：H100 / GB200；
- OS：Ubuntu；
- 业务意图：Training / Inference；
- 平台：Kubeflow / Dynamo。

然后它会生成一份对应的 recipe，里面包含已知可行的组件版本与配置组合。

### 2. Overlay

Overlay 可以理解为分层配置模型。AICR 不是从零拼出一份超长 values 文件，
而是把配置拆成不同层次：

- 基础默认层；
- 云平台层；
- 加速卡层；
- OS 层；
- 工作负载层。

这样做的价值很大：平台团队终于可以用“组合”而不是“复制粘贴”去管理 GPU 集群基线。

### 3. Bundle

Bundle 是把 recipe 进一步物化后的部署产物。AICR 会输出适合部署的目录结构，
其中包含每个组件的 Helm chart、values、checksum 和说明文件。

这意味着 recipe 不只是“文档建议”，而是可以直接进入 GitOps 流程的工件。

## AICR 的工作流长什么样？

从官方 README 看，AICR 的主流程很清晰：

```bash
# 1. 采集当前集群状态
aicr snapshot --output snapshot.yaml

# 2. 生成目标环境对应的 recipe
aicr recipe --service eks --accelerator h100 --os ubuntu \
  --intent training --platform kubeflow -o recipe.yaml

# 3. 用 snapshot 校验 recipe 和现网是否匹配
aicr validate --recipe recipe.yaml --snapshot snapshot.yaml

# 4. 渲染为可部署工件
aicr bundle --recipe recipe.yaml --output ./bundles
```

这背后的思路非常工程化：

- **snapshot** 负责采集“现状”；
- **recipe** 负责描述“目标状态”；
- **validate** 负责比较现状和目标之间是否偏离；
- **bundle** 负责把目标状态转成真正可部署的产物。

这套模型很适合做平台标准化，也适合在交付、升级和审计场景里使用。

## AICR 的几个核心组件

官方文档里主要有三个组件：

### `aicr` CLI

主入口。负责生成 recipe、采集 snapshot、校验配置、输出 bundle。

### `aicrd`

一个 REST API 服务，能力和 CLI 对齐。更适合放到 CI/CD 或集群内服务里，
也更方便做自动化集成。

### Snapshot Agent

以 Kubernetes Job 的方式运行，用来收集当前集群中的 GPU、驱动、OS、
Operator 等状态，再写入 ConfigMap 供后续校验。

从平台工程视角看，这个设计是合理的：**CLI 适合人工操作与本地流水线，
API/Agent 适合集群内自动化。**

## 它和 GPU Operator、DRA 是什么关系？

这是 AICR 最容易被误解的地方。

### AICR 不是 GPU Operator 的替代品

GPU Operator 负责的是**节点级 GPU 生命周期管理**，比如驱动、device plugin、
监控组件等的安装和维护。

AICR 站位更高，它负责的是：**把 GPU Operator 连同其他平台组件一起，
组织成一套经过验证的集群级部署配方。**

你可以把两者理解成：

- GPU Operator：管理单类 GPU 组件；
- AICR：编排整套 GPU 集群基线。

### AICR 也不是 DRA

DRA 解决的是 Kubernetes 中更灵活的设备资源分配问题，
属于资源模型和调度接口层面的能力。

AICR 则更偏向**集群安装与配置管理**。它不直接改变调度语义，
而是确保底层驱动、Operator、网络和附属组件以已验证的组合落地。

## 为什么这个项目值得 AI Infra 工程师关注？

我认为 AICR 的价值不只在“省一点安装时间”，而是它代表了一种更成熟的平台思路。

### 1. 把隐性经验变成显性工件

很多 GPU 集群最佳实践长期停留在内部脚本、runbook 和个人经验中。
AICR 把这些知识变成 recipe，这意味着它终于可以被版本管理、审计、复用和自动化消费。

### 2. 让 GitOps 真正覆盖到集群基线

很多团队已经用 GitOps 管应用，但 GPU 集群底层组件仍然靠人工维护。
AICR 输出 bundle 之后，这部分也更容易纳入统一交付流程。

### 3. 给升级和验收提供了“参照物”

升级 GPU 驱动、Operator 或 K8s 版本时，最怕的是“改完能跑，但不确定是不是官方验证组合”。
AICR 的 recipe 和 validate 机制，至少提供了一个明确的对照基线。

### 4. 对多环境复制尤其友好

如果你的平台要在多个区域、多个客户环境、多个云之间复制，recipe 模型会比手工维护 values 文件更稳。

## 当前阶段也要看清它的边界

AICR 很有潜力，但它现在不是“万能平台”。

从官方 README 和本次 AI-Infra 合并 PR 看，目前它有几个明显边界：

- **不是集群创建器**：它不负责创建控制平面或云资源；
- **不是完整发行版**：它不取代 EKS、GKE、OpenShift 这类产品；
- **支持矩阵还比较有限**：当前主要覆盖 EKS、GKE、Kind，H100/GB200，Ubuntu；
- **工作负载场景仍偏聚焦**：训练以 Kubeflow 为主，推理以 Dynamo 为主；
- **项目仍然较新**：生态成熟度、组件覆盖度和社区反馈还在早期阶段。

所以更准确的定位应该是：
**AICR 不是让你“从零拥有一个 AI 平台”，而是让你更稳定地交付一套 GPU 集群运行时基线。**

## 供应链安全这点也值得注意

官方 README 里还强调了几项供应链安全能力：

- SLSA Level 3 provenance；
- 签名的 SBOM；
- cosign image attestation；
- 对组件做 checksum 校验。

这说明 NVIDIA 并不只是把它当“安装脚本工具”，而是在朝着**可审计、可验证的交付工件**
方向设计。对于企业平台团队来说，这一点很重要，因为 GPU 集群的组件链条通常比普通应用长得多。

## 我对 AICR 的判断

如果只用一句话概括，我会这样描述 AICR：

**它是在尝试把“GPU 集群怎么装才靠谱”这件事，从经验主义变成产品化、声明式、可验证的工程流程。**

这类项目短期内未必直接改变调度器、推理引擎或训练框架的能力边界，
但它会影响 AI 平台真正落地时最容易被低估的一层：**集群基线的一致性与可复制性**。

对平台工程师来说，AICR 值得持续观察的，不只是它支持了哪些组件，
更是它能否逐步形成一个被社区接受的“已验证 GPU 集群组合”分发模型。

如果这条路走通，未来很多 GPU 平台交付工作，可能会越来越像“选择 recipe 并校验差异”，
而不是从一个巨大的 Excel 兼容矩阵开始。

## 总结

NVIDIA AICR 是一个很典型的 AI Infra 新项目：它不花哨，但切中平台团队的痛点。
在 GPU 集群越来越复杂、版本组合越来越难控的背景下，**把验证过的集群配置沉淀成 recipe，
再输出成可部署、可校验、可审计的工件**，这件事本身就很有价值。

如果你正在做以下工作，AICR 特别值得关注：

- Kubernetes 上的训练或推理平台建设；
- GPU 集群标准化交付；
- 多环境复制和 GitOps 平台治理；
- GPU Operator、网络组件和系统基线的兼容性管理。

它现在还处于早期阶段，但方向是对的。

## 参考

- [NVIDIA/aicr GitHub 仓库](https://github.com/NVIDIA/aicr)
- [AI-Infra PR #252: Add NVIDIA AI Cluster Runtime (AICR) to AI-Infra landscape and docs](https://github.com/pacoxu/AI-Infra/pull/252)
