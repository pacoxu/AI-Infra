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

本文基于截至 **2026-05-13** 的公开资料，仅用于技术参考。不同方案的实际效果高度依赖业务负载、GPU 与网络拓扑、现有控制面、团队运维能力与生态绑定方式。项目当前设计不代表最终形态，社区开放度、活跃度和与上游生态的融合方向，通常比单个版本里的功能表更重要。

## 先说结论

今天做推理编排选型，最容易犯的错误不是“选错项目”，而是把**不同层的东西拿来横向比较**：

- `vLLM`、`SGLang` 更接近 **runtime / 推理引擎**
- `vLLM Production Stack`、`llm-d` 更接近 **serving stack**
- `KServe`、`AIBrix`、`Kthena`、`Dynamo` 更接近 **平台 / control plane**
- `RBG`、`LWS/DisaggregatedSet` 更接近 **workload primitive / 编排 API**

如果只给一句最短建议：

- 已经深度使用 `Volcano`：优先看 `Kthena`
- 已经标准化 `KServe`：优先看 `KServe + llm-d`
- 纯 `vLLM` 团队且想先上最轻一层：优先看 `vLLM Production Stack`
- 以 `NVIDIA` 集群和性能系统能力为第一优先级：优先看 `Dynamo`
- 希望在 vanilla Kubernetes 上组合平台组件：优先看 `AIBrix`
- 已经以 `SGLang` 为 runtime：优先看 `SGLang Model Gateway`；如果还要 Kubernetes 上的一等多角色 workload API，再看 `RBG`

## 1. 过去一年最大的变化

2025 年这个话题常被讲成“大家都在做 PD 分离”。到 2026 年，这个说法已经不够用了。当前的主线更准确地说是：

- 不是只解决“怎么起 Pod”，而是解决 **role-aware orchestration**
- 不是只做 prefill/decode，而是把 **routing、KV、autoscaling、topology、failure handling** 一起纳入系统设计
- 不是只选一个 CRD，而是在选一套 **runtime + serving + control plane + scheduling** 的组合

几个旧印象已经需要更新：

- `AIBrix` 不再是 “KubeRay 用户的方案”。官方安装文档已经明确：`KubeRay` 是可选组件，不装也能用 `StormService` 跑单机和多节点推理。
- `Dynamo` 也不适合再简单概括成 “Grove 模式或 LWS 模式”。它已经形成了 `DGDR/DGD + Operator + Planner + Grove` 的 Kubernetes 路线。
- `KServe` 与 `llm-d` 也不宜再理解成互斥关系。`KServe 0.17` 文档已经明确写出 `LLMInferenceService` built on `llm-d`。
- `SGLang` 不只是 runtime。最新文档里的 `Model Gateway` 已经覆盖路由、Kubernetes service discovery、PD topology、可靠性控制和 Inference Gateway Mode。

## 2. 先按层来拆，而不是按名字比

| 层次 | 代表项目 | 更像什么 |
| --- | --- | --- |
| Runtime / 引擎 | `vLLM`、`SGLang` | 在单 Pod 或多 Pod 内执行推理 |
| Serving Stack | `vLLM Production Stack`、`llm-d` | 把 runtime 扩展成可部署、可路由、可观测的集群级服务 |
| Platform / Control Plane | `KServe`、`AIBrix`、`Kthena`、`Dynamo` | 用 CRD、router、autoscaler、policy 去统一管理推理生命周期 |
| Workload Primitive | `RBG`、`LWS/DisaggregatedSet` | 为多角色、多节点、强协作 workload 提供更合适的 Kubernetes API |

这个分层视角会直接影响你的选型逻辑：

- 如果你在找的是“统一入口和治理能力”，就应该优先比较 `KServe / AIBrix / Kthena / Dynamo`
- 如果你在找的是“高性能分布式 serving 方案”，重点应放在 `llm-d / vLLM Production Stack / SGLang Gateway`
- 如果你在找的是“多角色 workload API”，那就更该看 `RBG / LWS / DisaggregatedSet`

## 3. KServe：更像统一 AI 推理平台，而不是单一 runtime 包装器

截至 `2026-05-13`，KServe 官网已经把自己定位成 **Standardized Distributed Generative and Predictive AI Inference Platform**。它当前最重要的变化不是“能跑 LLM 了”，而是把 Generative 路线单独做成了 `LLMInferenceService`。

从官方 `0.17` 文档看，`LLMInferenceService` 的关键信号非常明确：

- 它是面向 Generative AI 的独立 CRD，不再把 LLM 只塞进传统 `InferenceService`
- 它直接建立在 `llm-d` 之上
- 它在平台层暴露了多节点、PD 分离、Advanced Routing、DP+EP 等能力
- 它同时保留了 KServe 一贯擅长的统一 API、生命周期管理、Gateway API 集成和企业运维治理

这意味着，今天很多场景下你不该再问 “KServe or llm-d”，而更应该问：

`KServe` 是否是我想要的控制面，`llm-d` 是否是我愿意接受的底层 distributed serving stack？

如果你已经有：

- `Knative/KServe` 经验
- 标准 Kubernetes API 驱动的模型交付流程
- 统一流量入口、配额、网关策略、团队边界

那么 `KServe + llm-d` 往往是最自然的组合。

## 4. llm-d：高性能 distributed serving stack

`llm-d` 的位置越来越清楚了。它不是通用平台，也不是单纯的 vLLM deployment 模板，而是一个 **Kubernetes-native distributed inference serving stack**。

截至 `2026-05-12` 发布的 `v0.7.0`，官方 release 和文档显示它的核心能力已经比较完整：

- Router / Scheduler 作为一等组件
- KV cache aware routing
- Prefill/Decode disaggregation
- LeaderWorkerSet 作为多节点编排路径之一
- variant autoscaler
- 与 Gateway API inference extension 的整合
- 新增更完整的 `SGLang` well-lit path

它的价值主要在“集群级智能”，而不是“单 Pod 里把 kernel 跑得更快”：

- 请求是否命中前缀缓存
- prefill 和 decode 是否落在最合适的资源池
- router 是否能做更细粒度 endpoint 选择
- 多租户和大模型场景下的 tail latency 与 GPU 利用率如何控制

如果你已经认定：

- 需要 cluster-wide cache aware routing
- 需要 role-aware / PD-aware serving
- 需要比 `vLLM + Service` 更强的集群级调度智能

那么 `llm-d` 是目前最清晰的一条路线之一。

## 5. vLLM Production Stack：更轻的 upstream reference stack

`vLLM Production Stack` 不应和 `llm-d`、`KServe`、`Dynamo` 放在同一层理解。它在官方 README 中的定位更朴素：**vLLM’s reference system for K8S-native cluster-wide deployment**。

截至 `2026-05-07`，最新 release 是 `vllm-stack-0.1.11`。当前公开形态的重点是：

- Helm 驱动的部署方式
- request router
- Prometheus + Grafana observability
- LMCache / KV cache offloading
- 在不改应用代码的前提下，从单实例扩到分布式 vLLM

这条路线的优点很明确：

- 对已经标准化 `vLLM` 的团队最友好
- 栈更薄，更像 reference stack 而不是完整平台
- 能较快落地基础的路由、观测和 cache offloading

它的边界也同样明确：

- 它不是统一 control plane
- 它不试图提供 `KServe / AIBrix / Kthena / Dynamo` 那样的完整平台治理能力
- 它更适合作为“先用起来”的起点，而不是“一次性解决所有多角色编排问题”的终点

如果你只想回答“如何更稳妥地在 Kubernetes 上部署一套 upstream vLLM 集群”，那它是很合理的第一站。

## 6. SGLang 与 RBG：runtime/gateway 和 workload API 要分开看

这两者最容易被混成一个东西，但实际上不是同一层。

### 6.1 SGLang：高性能 runtime，外加越来越完整的 Model Gateway

SGLang 官方文档当前已经同时强调两件事：

- 它本身是高性能 serving framework，支持 PD disaggregation、HiCache、多种并行方式、广泛硬件平台
- 它现在还有 `SGLang Model Gateway`，提供 HTTP/gRPC/OpenAI-compatible 路由、Kubernetes service discovery、PD topology、可靠性控制、观测与 Inference Gateway Mode

截至 `2026-05-05` 的 `v0.5.11` release，SGLang 又强化了一个重要方向：**统一 Inference Gateway Mode**。这意味着它不仅是一个 runtime，也越来越像“自带 gateway 的 serving stack”。

所以，如果你的团队已经明确站在 `SGLang` 路线上，第一选择往往不是“换个平台”，而是：

- 先用 `SGLang runtime`
- 再用 `SGLang Model Gateway` 扩展成可运维的集群入口

### 6.2 RBG：多角色 workload primitive

`RBG` 的价值不在于当 gateway，而在于提供 `RoleBasedGroup` 这种更适合分布式推理服务的 Kubernetes workload API。

它 README 里公开强调的点包括：

- role startup-order dependencies
- auto service discovery
- group/role 级 elastic scaling
- atomic rollout
- topology-aware placement
- atomic failure recovery
- 可定制 workload backend，包括 `StatefulSet`、`Deployment`、`LeaderWorkerSet`

所以更准确的定位是：

- `SGLang` 解决 runtime 和 gateway
- `RBG` 解决多角色 workload 如何在 Kubernetes 上被表达和编排

如果你是 `SGLang` 用户，又觉得 `Deployment/StatefulSet` 对多角色服务表达不够好，`RBG` 就值得重点看。

## 7. AIBrix：模块化的 GenAI 基础设施平台

`AIBrix` 当前更像“模块化平台”，而不是单一 CRD。

截至 `2026-03-03` 的 `v0.6.0` 与最新文档，几个信号已经很明确：

- 官方安装文档明确支持 vanilla Kubernetes
- `Envoy Gateway` 是前置依赖
- `KubeRay` 变成可选组件
- `StormService` 是其多节点编排主线之一
- `Router`、`KV cache`、`PodAutoscaler`、`LoRA/Adapter` 等能力都在平台内独立演进

`StormService` 的价值在于，它不是单纯的 prefill/decode 模板，而是明确设计成三层结构：

- `StormService`
- `RoleSet`
- `Pods`

并且它同时支持：

- replica mode
- pooled mode
- top-level rolling / inplace update
- RoleSet 级 parallel / sequential / interleaved update

更重要的是，AIBrix 当前文档已经明确支持 pooled mode 下的 **role-level autoscaling**。这一点和很多只会说“支持 PD”的项目相比，工程含义更大，因为它真正触及了不同 role 负载形状不同这一现实。

如果你的偏好是：

- vanilla Kubernetes
- 组件化平台
- Router、Autoscaler、KV、LoRA 都希望是平台一部分
- 不想深度绑定 `Volcano` 或 NVIDIA 自家整栈

那么 `AIBrix` 是很强的候选。

## 8. Kthena：Volcano 原生的完整推理控制面

Kthena 到现在已经不是一个“Volcano 旁边的实验项目”了。`v0.4.0` 官方文档把它定义得很直接：**Kubernetes-native AI serving platform**。

它当前的特点，不是“也支持 PD”，而是把下面这些能力组织到了一套面向服务的平台抽象里：

- `ModelBooster`
- `ModelRoute`
- `ModelServer`
- `ModelServing`
- `AutoScalingPolicy`
- `AutoScalingPolicyBinding`

从当前文档和官方博客看，Kthena 的强项在于：

- 与 `Volcano` 调度生态天然亲和
- 面向多后端引擎，包括 `vLLM`、`SGLang`、`Triton`、`TorchServe`
- request-level intelligent routing
- token-based rate limit、canary、failover
- role-aware PD routing
- 多指标、成本驱动 autoscaling

另外，Kthena 的一个重要变化是它对 LWS 的态度。公开 proposal 与后续 PR 说明，它并不是排斥 `LeaderWorkerSet`，而是在探索 **LWS API compatibility**，把 LWS 视作一个可兼容的 northbound 接口，而不是唯一底层 primitive。

这意味着如果你已经站在：

- `Volcano`
- gang scheduling
- topology-aware placement
- heterogenous accelerator orchestration

这一侧，那么 Kthena 往往比其他方案更“原生”。

## 9. Dynamo：性能系统优先的推理平台

`Dynamo` 现在最不应该被简化成“一个编排器”。从官方文档看，它已经明显是一整套平台：

- `DynamoGraphDeploymentRequest (DGDR)`：推荐的、简化的 SLA 驱动入口
- `DynamoGraphDeployment (DGD)`：更直接的底层配置入口
- `Planner`
- `Profiler`
- `Router`
- `KVBM`
- 与 `Grove` 的多节点编排整合

官方 Kubernetes deployment guide 和 Grove 文档显示，Dynamo 当前的思路非常清楚：

- 平台层由 `DGDR/DGD + Operator` 承担
- 多节点、多角色编排主要交给 `Grove`
- `Planner` 负责围绕 SLA 生成和调整部署形态

`Grove` 这条线尤其值得注意。它公开把自己定义成：

- 专门为现代 AI workload，特别是 disaggregated inference 设计的 Kubernetes API
- 能在单个资源中表达 prefill、decode、routing 等多个 component
- 支持 multi-level horizontal autoscaling、startup dependencies、topology-aware scheduling

所以今天更准确的说法不是 “Dynamo 有 Grove 模式和 LWS 模式”，而是：

`Dynamo` 已经把性能系统、平台入口和 Kubernetes 编排主线组织起来了，而 `Grove` 是其中面向多角色、多节点编排的核心一环。

如果你主要是：

- `NVIDIA` 集群
- 大模型、多节点、强 SLA 驱动
- 更在意 profiler / planner / backend / KV 路径的一体化

那么 `Dynamo` 的吸引力仍然最大。

## 10. 一个更有意义的对比表

| 方案 | 本质定位 | `role / PD` | 路由与网关 | 扩缩容 | 生态重心 |
| --- | --- | --- | --- | --- | --- |
| `KServe` | 统一 AI inference 平台 | 强，但更多通过 `LLMInferenceService` 暴露 | 强，Gateway API 与 AI Gateway 明确成型 | 强 | 标准 K8s 平台、KServe 用户 |
| `llm-d` | distributed serving stack | 很强 | 很强 | 强 | 高性能分布式 LLM serving |
| `vLLM Production Stack` | upstream reference stack | 有，但不是它当前最突出的卖点 | 中到强 | 中 | 纯 `vLLM` 用户 |
| `SGLang` | runtime + gateway | 很强 | 很强 | 中到强 | `SGLang` runtime 用户 |
| `RBG` | multirole workload API | 核心能力 | 以 service discovery 为主 | 强 | 需要通用多角色 primitive 的团队 |
| `AIBrix` | 模块化 GenAI infra 平台 | 很强，`StormService/RoleSet` 已较成熟 | 强 | 强，role-level autoscaling 已落地 | vanilla Kubernetes + 平台组件组合 |
| `Kthena` | Volcano-native AI serving platform | 很强，`ModelServing/ServingGroup/Role` | 很强 | 很强 | Volcano / 调度与拓扑优先 |
| `Dynamo` | performance-first AI infra platform | 很强，`DGDR/DGD + Grove` | 很强 | 很强，Planner 能力突出 | NVIDIA / 多节点 / SLA 驱动 |

## 11. 怎么选：按你已有基础设施来

下面给一个简化版决策指南。真实场景里还要考虑模型形态、GPU 代际、网络拓扑、成本模型、平台团队能力和多租户边界。

### 如果你已经是 Volcano 用户

优先看 `Kthena`。

原因不是“它也支持推理”，而是它的调度与平台抽象天然站在同一个生态里。你会更容易把：

- gang scheduling
- topology-aware scheduling
- 推理 role 编排
- route/scale/policy

放进一条统一链路。

### 如果你已经是 KServe 用户

优先看 `KServe + llm-d`，而不是把两者当成二选一。

`KServe` 更像 control plane，`llm-d` 更像 distributed intelligence / serving stack。对于已经围绕 `InferenceService`、Gateway API、平台治理构建流程的团队，这通常是最自然的升级路径。

### 如果你主要是 vLLM 用户

先问自己要的是“最轻方案”还是“最强 serving stack”：

- 想先快速得到一套 upstream 参考部署：`vLLM Production Stack`
- 已经明确需要 cache-aware routing、PD、cluster-level intelligence：`llm-d`

### 如果你主要是 NVIDIA 集群

优先看 `Dynamo`，尤其是：

- 多节点大模型
- 强 SLA 驱动
- 希望用 profiler / planner 来辅助配置选择
- 希望 route、KV、backend、orchestration 一起优化

### 如果你是 vanilla Kubernetes 团队

优先看 `AIBrix`。

它目前在“平台组件化”和“不过度绑定某个单一调度器”之间的平衡比较清晰。你可以更自然地组合：

- `Envoy Gateway`
- `StormService`
- `Router`
- `PodAutoscaler`
- `KV Cache`

### 如果你是 SGLang 用户

优先顺序通常是：

1. `SGLang runtime`
2. `SGLang Model Gateway`
3. 如果还需要更强的 Kubernetes 多角色 workload API，再补 `RBG`

换句话说，`SGLang` 与 `RBG` 更像上下配合，而不是互相替代。

### 如果你想要更“上游 primitive”的路线

可以重点关注：

- `RBG`
- `LWS + DisaggregatedSet`

这一层的价值在于 workload API，而不是完整平台。

## 12. PD 分离仍然不是默认答案

这一点到今天依然成立。

虽然这几个方向几乎都在强化 `prefill/decode` 分离，但“支持 PD”不等于“PD 一定值得”。

更适合引入 PD 的情况通常包括：

- 长 prompt、短输出
- 高并发，且请求形状差异大
- prefill 与 decode 对硬件偏好明显不同
- 你确实要单独优化 `TTFT` 与 `TPOT`

更应该谨慎的情况包括：

- 短上下文或中小模型
- 低并发
- 同构硬件
- KV 传输和跨 role 协调成本可能吞掉收益
- 团队目前还没有足够观测与运维能力

今天的进步主要是：平台终于开始把 PD 从“实验室技巧”做成“可运维能力”。但它仍然不是银弹。

## 结语

截至 `2026-05-13`，这个领域的主线已经不是“谁支持 PD”，而是“谁能把 role-aware orchestration、routing、autoscaling、topology 和 failure handling 组织成一套可落地的系统”。

所以真正要回答的，不只是 “AIBrix or Kthena or Dynamo”，而是：

- 你是在选 **runtime**、**serving stack**、**平台**，还是 **workload API**
- 你更在意 **生态兼容**，还是 **性能系统能力**
- 你是想贴近 **上游通用抽象**，还是接受某个生态更强的整栈绑定

如果只保留一句话：

- 想要模块化平台：`AIBrix`
- 想要 Volcano 原生推理控制面：`Kthena`
- 想要性能系统优先、尤其是 NVIDIA 路线：`Dynamo`
- 想要 K8s 上高性能 distributed serving：`llm-d`
- 想先上最轻的 upstream vLLM 参考栈：`vLLM Production Stack`
- 已经是 SGLang 体系：`SGLang Gateway + RBG`
