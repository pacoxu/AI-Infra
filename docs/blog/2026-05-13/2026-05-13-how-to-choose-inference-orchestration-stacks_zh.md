---
status: Active
maintainer: pacoxu
date: 2026-05-13
tags: inference, orchestration, kubernetes, llm, pd-disaggregation, llm-d, kserve, dynamo, aibrix, kthena, sglang, rbg, vllm
canonical_path: docs/blog/2026-05-13/2026-05-13-how-to-choose-inference-orchestration-stacks_zh.md
source_urls:
  - https://kserve.github.io/website/
  - https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview
  - https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-envoy-ai-gateway
  - https://kserve.github.io/website/blog/cloud-native-ai-inference-kserve-llm-d
  - https://github.com/llm-d/llm-d
  - https://github.com/llm-d/llm-d/releases
  - https://llm-d.ai/docs/architecture/architecture
  - https://github.com/vllm-project/production-stack
  - https://github.com/vllm-project/production-stack/releases
  - https://docs.vllm.ai/en/latest/deployment/integrations/production-stack.html
  - https://github.com/vllm-project/aibrix
  - https://github.com/vllm-project/aibrix/releases
  - https://aibrix.readthedocs.io/latest/getting_started/installation/installation.html
  - https://aibrix.readthedocs.io/latest/designs/aibrix-stormservice.html
  - https://aibrix.readthedocs.io/latest/designs/aibrix-router.html
  - https://aibrix.readthedocs.io/latest/features/autoscaling/metric-based-autoscaling.html
  - https://kthena.volcano.sh/docs/intro
  - https://kthena.volcano.sh/docs/v0.2.0/architecture
  - https://github.com/volcano-sh/kthena/blob/main/docs/proposal/modelserving-role-support-leaderworkerset.md
  - https://github.com/volcano-sh/kthena/pull/767
  - https://volcano.sh/en/blog/introducing-kthena-redefining-llm-inference-for-the-cloud-native-era/
  - https://docs.nvidia.com/dynamo/latest/kubernetes-deployment/deployment-guide
  - https://docs.nvidia.com/dynamo/latest/kubernetes-deployment/multinode/grove
  - https://docs.nvidia.com/dynamo/components/planner/planner-guide
  - https://github.com/ai-dynamo/dynamo
  - https://docs.sglang.io/
  - https://docs.sglang.io/advanced_features/router.html
  - https://github.com/sgl-project/sglang/releases
  - https://github.com/sgl-project/rbg
  - https://github.com/kubernetes-sigs/lws/blob/main/keps/766-DisaggregatedSet/README.md
---

# 推理编排方案如何选择？AIBrix、Kthena、Dynamo、llm-d、KServe、vLLM Production Stack 与 SGLang/RBG

本文基于截至 **2026-05-13** 的公开资料，仅用于技术参考。不同方案的实际效果高度依赖业务负载、GPU 与网络拓扑、现有控制面、运维方式与生态绑定程度。项目当前设计不代表最终形态，社区开放度、活跃度与长期演进方向，通常比单个版本里的功能表更重要。

## 摘要

当前公开资料里，这些项目更适合先按层理解，再做横向对比：

- `vLLM`、`SGLang` 更接近 **runtime / 推理引擎**
- `vLLM Production Stack`、`llm-d` 更接近 **serving stack**
- `KServe`、`AIBrix`、`Kthena`、`Dynamo` 更接近 **平台 / control plane**
- `RBG`、`LWS/DisaggregatedSet` 更接近 **workload primitive / 编排 API**

从当前公开资料看：

- `KServe` 已经把 Generative AI 路线单独落到 `LLMInferenceService`，并明确建立在 `llm-d` 之上
- `llm-d` 正在向更完整的 distributed serving stack 收敛，重点在路由、KV locality、PD 和集群级调度智能
- `vLLM Production Stack` 当前定位仍是 upstream 参考部署栈，而不是统一控制面
- `SGLang` 同时覆盖 runtime 和 gateway；`RBG` 负责多角色 workload API
- `LWS/DisaggregatedSet` 开始把多角色、多 LWS 的协调更新和版本感知服务编排做成上游 primitive
- `AIBrix`、`Kthena`、`Dynamo` 都在朝完整平台演进，只是各自绑定的生态与优化重点不同

## 1. 当前格局

当前推理编排方案普遍在处理同一组系统问题：

- **角色编排**：prefill、decode、router、gateway 等角色如何表达与协同
- **流量入口**：请求如何按拓扑、缓存命中、版本状态和负载分布路由
- **KV 与状态管理**：跨副本、跨角色、跨节点的数据局部性如何维持
- **扩缩容**：是否按 role、按 workload、按 SLA、按平台策略独立扩缩
- **升级与恢复**：多角色服务如何协调 rollout、回滚和故障恢复

从公开资料看，可以先做如下归类：

- `KServe` 当前是统一平台入口
- `llm-d` 当前是分布式 serving 主线之一
- `vLLM Production Stack` 当前是较轻的 upstream 部署栈
- `SGLang` 当前同时覆盖 runtime 与 gateway
- `RBG`、`DisaggregatedSet` 当前更偏上游 workload API
- `AIBrix`、`Kthena`、`Dynamo` 当前都在形成各自的平台路径

## 2. 分层视角

| 层次 | 代表项目 | 主要职责 |
| --- | --- | --- |
| Runtime / 引擎 | `vLLM`、`SGLang` | 在单 Pod 或一组 tightly-coupled Pod 内执行推理 |
| Serving Stack | `vLLM Production Stack`、`llm-d` | 把 runtime 组织成可部署、可路由、可观测的集群级服务 |
| Platform / Control Plane | `KServe`、`AIBrix`、`Kthena`、`Dynamo` | 用 CRD、router、autoscaler、policy 去统一管理推理生命周期 |
| Workload Primitive | `RBG`、`LWS/DisaggregatedSet` | 为多角色、多节点、强协作 AI workload 提供更合适的 Kubernetes API |

这个分层直接决定了比较方式：

- `KServe / AIBrix / Kthena / Dynamo` 更适合放在平台层对比
- `llm-d / vLLM Production Stack / SGLang Gateway` 更适合放在 serving stack 层对比
- `RBG / LWS / DisaggregatedSet` 更适合放在 workload primitive 层对比

## 3. KServe

截至 `2026-05-13`，KServe 官网把自己定位成 **Standardized Distributed Generative and Predictive AI Inference Platform**。当前 Generative AI 路线明确落到 `LLMInferenceService`。

从公开 `0.17` 文档可以看到几件事：

- `LLMInferenceService` 是面向 Generative AI 的独立 CRD
- 它明确建立在 `llm-d` 之上
- 它在平台层暴露了多节点推理、PD 分离、Advanced Routing、DP+EP 等能力
- 它仍保留 KServe 一贯的统一 API、生命周期管理、Gateway API 集成和平台治理方式

因此，当前更准确的理解不是“`KServe` 或 `llm-d`”，而是：

- `KServe` 负责平台入口与治理
- `llm-d` 负责底层 distributed serving 能力

在标准 Kubernetes 平台、统一模型交付流程和 Gateway API 路线中，这是一组比较自然的组合。

## 4. llm-d

`llm-d` 当前更接近 **Kubernetes-native distributed inference serving stack**，而不是通用平台，也不是单纯的 `vLLM` 部署模板。

截至 `2026-05-12` 发布的 `v0.7.0`，公开材料显示它的主线已经比较完整：

- Router / Scheduler 作为一等组件
- KV cache aware routing
- Prefill/Decode disaggregation
- `LeaderWorkerSet` 作为多节点编排路径之一
- variant autoscaling
- 与 Gateway API inference extension 的整合
- 更清晰的 `SGLang` 支持路径

它的重点在于集群级智能，而不是单个 runtime Pod 的性能本身：

- 请求是否保留前缀缓存局部性
- prefill 和 decode 是否落在合适的资源池
- router 是否能做比通用负载均衡更细的 endpoint 选择
- 多租户和大模型场景下的 tail latency 与 GPU 利用率如何控制

## 5. vLLM Production Stack

`vLLM Production Stack` 当前定位是 **upstream 参考部署栈**。官方 README 的定位是 **vLLM’s reference system for K8S-native cluster-wide deployment**。

截至 `2026-05-07`，最新 release 是 `vllm-stack-0.1.11`。当前公开形态主要包括：

- Helm 部署
- request router
- Prometheus + Grafana observability
- LMCache / KV cache offloading
- 从单实例扩展到 cluster-wide vLLM 的参考路径

它的特点比较清楚：

- 更接近 upstream `vLLM`
- 栈更薄
- 路由、观测与 cache offloading 已经具备基础能力

同时，它当前并不试图承担统一 control plane 的角色，也不提供 `KServe / AIBrix / Kthena / Dynamo` 那种完整平台治理面。

## 6. SGLang、RBG 与 LWS/DisaggregatedSet

这一组更适合放在一起理解，因为它们分别覆盖 runtime、gateway 与 workload primitive。

### 6.1 SGLang

SGLang 当前同时覆盖 runtime 与 gateway。

最新公开文档与 release 说明，当前重点包括：

- 高性能 serving framework
- PD disaggregation、HiCache、多种并行方式和广泛硬件支持
- `SGLang Model Gateway`，覆盖 HTTP/gRPC/OpenAI-compatible 路由、Kubernetes service discovery、PD topology、观测与可靠性控制
- `Unified Inference Gateway Mode`

因此，SGLang 在这里同时覆盖两层：

- runtime 层能力较强
- 同时在向 serving stack 方向延展

### 6.2 RBG

`RBG` 的重点不在 gateway，而在 `RoleBasedGroup` 这种多角色 workload API。

其 README 公开强调的能力包括：

- role startup-order dependencies
- automated service discovery
- group-level 与 role-level elastic scaling
- atomic rollout
- topology-aware placement
- atomic failure recovery
- 多种 role backend，包括 `StatefulSet`、`Deployment`、`LeaderWorkerSet`

这意味着 `RBG` 主要解决的是：如何把多角色推理服务表达成 Kubernetes workload primitive。

### 6.3 LWS / DisaggregatedSet

`DisaggregatedSet` 是 `LeaderWorkerSet` 项目提出的新 CRD，目标是把原本需要人工协调的多个 `LeaderWorkerSet` 收敛成一个统一对象。

从 KEP-766 当前公开草案看，它要解决的核心问题是：

- 多个 LWS 的升级如何协调
- 多角色服务的版本一致性如何保证
- revision-aware Service 如何自动生成
- 多角色 rollout 如何避免孤儿工作负载和配置漂移

当前公开设计里，几个点比较关键：

- **`spec.roles`**：每个 role 内嵌完整的 `LeaderWorkerSetTemplateSpec`
- **N 维协调式滚动更新**：多个角色按统一 revision 与步骤推进，而不是各自独立 rollout
- **每 revision 的 headless Service**：例如 `{name}-{revision}-{role}-prv`，为 `llm-d` 这类上层路由器提供按 revision 比例路由的基础
- **当前边界**：暂不覆盖 HPA/VPA、多集群和非 LWS 后端

如果把 `RBG` 与 `DisaggregatedSet` 放在一起看，差别也比较清楚：

- `RBG` 更通用，role backend 可以不是 LWS
- `DisaggregatedSet` 更明确地站在 LWS 生态上，重点是多 LWS 的协调升级与服务编排

## 7. AIBrix

`AIBrix` 当前呈现为模块化平台设计，而不是单一 CRD。

截至 `2026-03-03` 的 `v0.6.0` 与最新文档，公开信号包括：

- vanilla Kubernetes 是一条明确路径
- `Envoy Gateway` 是前置依赖
- `KubeRay` 已经变成可选组件
- `StormService` 是其多节点编排主线之一
- router、KV cache、pod autoscaler、LoRA/adapter 等能力都在平台内独立演进

`StormService` 的关键点在于它不是单纯的 PD 模板，而是三层结构：

- `StormService`
- `RoleSet`
- `Pods`

当前公开设计还包括：

- replica mode
- pooled mode
- top-level rolling / inplace update
- RoleSet 级 parallel / sequential / interleaved update
- pooled mode 下的 role-level autoscaling

## 8. Kthena

Kthena 当前已经明确把自己定位成 **Kubernetes-native AI serving platform**。

它的主线不是“支持某一种 workload”，而是围绕一组平台抽象组织能力：

- `ModelBooster`
- `ModelRoute`
- `ModelServer`
- `ModelServing`
- `AutoScalingPolicy`
- `AutoScalingPolicyBinding`

从当前文档与官方博客看，Kthena 的几个特点比较稳定：

- 与 `Volcano` 调度生态亲和
- 支持多后端，包括 `vLLM`、`SGLang`、`Triton`、`TorchServe`
- request-level intelligent routing
- token-based rate limit、canary、failover
- role-aware PD routing
- 多指标、成本驱动 autoscaling

同时，公开 proposal 与后续 PR 也显示，Kthena 正在探索 **LWS API compatibility**。因此，LWS 在其中更接近兼容的 northbound 接口，而不是唯一底层 primitive。

## 9. Dynamo

`Dynamo` 当前定位是 **性能系统优先的推理平台**。

从官方文档看，它已经明显是一整套平台：

- `DynamoGraphDeploymentRequest (DGDR)`：推荐的、简化的 SLA 驱动入口
- `DynamoGraphDeployment (DGD)`：更直接的底层配置入口
- `Planner`
- `Profiler`
- `Router`
- `KVBM`
- 与 `Grove` 的多节点编排整合

Kubernetes deployment guide 与 Grove 文档显示，当前路线非常清楚：

- 平台层由 `DGDR/DGD + Operator` 承担
- 多节点、多角色编排主要交给 `Grove`
- `Planner` 负责围绕 SLA 生成和调整部署形态

`Grove` 自己公开强调的点也很直接：

- 面向现代 AI workload，尤其是 disaggregated inference
- 能在单个资源里表达 prefill、decode、routing 等多个 component
- 支持 multi-level horizontal autoscaling、startup dependencies、topology-aware scheduling

## 10. 对比

| 方案 | 定位 | `role / PD` | 路由与网关 | 扩缩容 | 生态重心 |
| --- | --- | --- | --- | --- | --- |
| `KServe` | 统一 AI inference 平台 | 强，通过 `LLMInferenceService` 暴露 | 强 | 强 | 标准 Kubernetes 平台 |
| `llm-d` | distributed serving stack | 很强 | 很强 | 强 | 高性能分布式 LLM serving |
| `vLLM Production Stack` | upstream reference stack | 有，但不是当前最突出的卖点 | 中到强 | 中 | 纯 `vLLM` 生态 |
| `SGLang` | runtime + gateway | 很强 | 很强 | 中到强 | `SGLang` runtime 与 gateway |
| `RBG` | multirole workload API | 核心能力 | 以 service discovery 为主 | 强 | 通用多角色 primitive |
| `LWS / DisaggregatedSet` | LWS 上层多角色 primitive | 很强 | 以 revision-aware Service orchestration 为主 | 当前扩缩边界较保守 | LWS 生态 |
| `AIBrix` | 模块化 GenAI infra 平台 | 很强，`StormService/RoleSet` 已较成熟 | 强 | 强，role-level autoscaling 已公开落地 | vanilla Kubernetes + 平台组件 |
| `Kthena` | Volcano-native AI serving platform | 很强，`ModelServing/ServingGroup/Role` | 很强 | 很强 | Volcano / 调度与拓扑 |
| `Dynamo` | performance-first AI infra platform | 很强，`DGDR/DGD + Grove` | 很强 | 很强，Planner 能力突出 | NVIDIA / 多节点 / SLA |

## 11. 场景观察

下面是一个简化版的场景观察，重点放在生态与基础设施关系，而不是抽象地讨论“谁更好”。

### Volcano 环境

`Kthena` 与 `Volcano` 的调度和平台抽象靠得最近，gang scheduling、topology-aware placement 和推理角色编排可以放在同一条链路中理解。

### KServe 环境

`KServe + llm-d` 是当前公开材料里较常见的组合：前者承担平台入口与治理，后者承担底层 distributed serving 能力。

### vLLM 环境

`vLLM Production Stack` 适合更轻的 upstream 部署路径；`llm-d` 更适合需要 cluster-wide routing、KV locality 和 PD orchestration 的场景。

### NVIDIA 环境

`Dynamo` 与 `Grove` 的组合更强调 profiler、planner、backend、KV 和多节点编排的一体化路径。

### vanilla Kubernetes 环境

`AIBrix` 当前在平台组件化方面最明确，`Envoy Gateway`、`StormService`、`Router`、`PodAutoscaler`、`KV Cache` 能组成较完整的控制面。

### SGLang 环境

`SGLang` 与 `RBG` 更像上下游关系：前者负责 runtime 与 gateway，后者负责多角色 workload API。

### 上游 primitive 路线

`RBG` 与 `LWS/DisaggregatedSet` 都值得关注，但侧重点不同：

- `RBG` 更通用
- `DisaggregatedSet` 更聚焦在 LWS 生态内的多角色协调更新与服务编排

## 12. PD 分离的适用边界

PD 分离当前已经不是单点技巧，而是一整套系统设计的一部分。但“支持 PD”不等于“PD 在所有场景都值得”。

更适合引入 PD 的情况通常包括：

- 长 prompt、短输出
- 高并发，且请求形状差异大
- prefill 与 decode 对硬件偏好明显不同
- `TTFT` 与 `TPOT` 需要分开优化

更需要谨慎评估的情况通常包括：

- 短上下文或中小模型
- 低并发
- 同构硬件
- KV 传输和跨 role 协调成本可能吞掉收益
- 平台观测、路由与故障处理能力尚未成型

## 结语

截至 `2026-05-13`，更适合的比较方式是先看各项目在推理系统里负责哪一层。

如果按这一视角归纳：

- `vLLM`、`SGLang` 主要是 runtime
- `vLLM Production Stack`、`llm-d` 主要是 serving stack
- `KServe`、`AIBrix`、`Kthena`、`Dynamo` 主要是平台
- `RBG`、`LWS/DisaggregatedSet` 主要是 workload primitive

这样再看各项目的角色、边界和组合关系，通常会比把所有名字放在同一层横向比较更清楚。
