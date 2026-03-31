---
status: Active
maintainer: pacoxu
date: 2026-04-06
tags: kubernetes, gpu, cold-start, ai-infrastructure, scheduling, serverless, inference
canonical_path: docs/blog/2026-04-06/2026-04-06-gpu-pod-cold-start-optimization_zh.md
source_urls:
  - https://github.com/pacoxu/AI-Infra/pull/281
  - https://www.cncf.io/blog/2026/03/27/the-weight-of-ai-models-why-infrastructure-always-arrives-slowly/
  - https://feisky.xyz/posts/2025-12-04-kubernetes%E8%B6%85%E5%A4%A7%E8%A7%84%E6%A8%A1%E9%9B%86%E7%BE%A4%E4%BA%91%E5%8E%82%E5%95%86%E5%A6%82%E4%BD%95%E4%B8%BAai%E8%AE%AD%E7%BB%83%E9%87%8D%E5%A1%91%E5%9F%BA%E7%A1%80%E8%AE%BE%E6%96%BD/
  - https://docs.cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/run-ai-model-streamer?hl=zh-cn
  - https://kubernetes.io/zh-cn/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/
  - https://kubernetes.io/blog/2026/01/02/kubernetes-v1-35-restart-all-containers/
  - https://kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale/
  - https://oneuptime.com/blog/post/2026-01-06-kubernetes-gpu-workloads-ml-ai/view
  - https://fluid-cloudnative.github.io/docs
  - https://www.volcengine.com/docs/6460/658947?lang=zh
  - https://zhuanlan.zhihu.com/p/1987152570653905705
---

# GPU Pod 冷启动优化：AI 工作负载的性能突破

这篇是对 `PR #281` 中「AI Pod 启动关键路径」的延续版，目标从“能拆解问题”进一步走到
“能在真实平台里落地”。

如果只记一句话：**冷启动优化不是单点提速，而是把 `调度等待 + 分发加载 + 运行时初始化`
变成可控预算。**

## 先说结论

AI 场景下可把启动时间拆成：

`T_total = T_capacity + T_schedule + T_image + T_model + T_runtime + T_warmup`

相比传统应用，AI 集群里最常见的大头通常不是 kube-apiserver，而是：

- `T_capacity`：节点/GPU 资源准备慢；
- `T_model`：模型权重加载慢；
- `T_warmup`：首轮编译与缓存预热慢。

这和 CNCF 文章里“infrastructure always arrives slowly”的观察一致：模型权重已经成为交付链路中的核心瓶颈，而不是边缘问题。

```mermaid
flowchart LR
  A["容量准备 T_capacity"] --> B["调度放置 T_schedule"]
  B --> C["镜像分发 T_image"]
  C --> D["模型加载 T_model"]
  D --> E["运行时初始化 T_runtime"]
  E --> F["预热完成 T_warmup"]
  F --> G["业务可服务"]
```

## 为什么 2026 年这个话题更急

从超大规模集群实践看（AWS 10 万节点、Google 13 万节点），“把 Pod 调起来”只是第一层，
真正难的是在大规模和多租户下，把昂贵 GPU 在**冷启动期间的空转**压到最低。

这意味着平台优化目标要从“秒级启动”改成“单位预算下的稳定可服务时间”：

- 离线训练关注吞吐和作业准入；
- 在线推理关注首请求延迟与可恢复时间；
- 训推混部关注抢占和队列切换时的抖动成本。

## 一张表看清：加速手段与适用边界

| 优化层 | 典型做法 | 主要收益 | 常见坑 |
| --- | --- | --- | --- |
| 容量与调度 | 大集群容量池、Kueue 队列、Gang 调度 | 降低 Pending 与排队时间 | 只调调度参数但不做容量预留 |
| 镜像分发 | 镜像预拉取、P2P 镜像加速、Lazy Pull | 降低 `T_image` | 节点 I/O 饱和、缓存击穿 |
| 模型加载 | Run:ai Model Streamer、Fluid 缓存 | 显著降低 `T_model` | 只测单模型，不测多租并发 |
| 运行时初始化 | 驱动/框架缓存复用、预热脚本 | 降低 `T_runtime/T_warmup` | Ready 过早放量导致抖动 |
| 生命周期变通 | VPA、就地重启全部容器 | 降低“必须重建 Pod”频率 | 把变通当作根治方案 |

## 模型加载是当前最高 ROI 区

在推理场景，`T_model` 往往占据冷启动大头。

GKE 文档给出了一条很实用的路径：`vLLM + --load-format=runai_streamer`，让权重从对象存储直接流式进入 GPU 内存，绕过“先下载本地再加载”的传统路径。文档里明确提到在其基准下可达到最高约 `6x` 的加载提速，并给出了可复现清单。

另一条路线是做数据/模型缓存编排：Fluid 的能力重点不在“只缓存一次”，而在于把缓存生命周期和调度联动起来，适合多任务共享热点模型。

实践建议：

1. 小模型高并发：优先做镜像与模型双缓存（命中率优先）。
2. 大模型低并发：优先做流式加载（缩短首个副本上线时间）。
3. 混合租户：把模型按热点分层，不要全量常驻。

## MIG 与 vGPU 不是一回事

很多“GPU 切分”方案被混在一起讨论，落地时会踩坑。可以用下面这张表区分：

| 维度 | MIG | vGPU / 时间切分类方案 |
| --- | --- | --- |
| 隔离方式 | 硬件级实例切分 | 虚拟化或时间片共享 |
| 显存边界 | 切片显存相对确定 | 常需处理显存竞争与回收 |
| 适用场景 | 稳态、可预测负载 | 弹性利用率优先场景 |
| 冷启动影响 | 切片准备和调度约束增加 | 恢复/迁移时可能出现显存回填与 offloading 成本 |

结论：如果你在做低延迟在线推理，先明确 SLA，再决定是否引入更激进的共享策略。否则“看起来 GPU 利用率高了”，但尾延迟和冷启动抖动会恶化。

## Serverless 与预热池：快，但要算账

Serverless 方向常见两条路：

1. 保留最小 GPU 资源池，缩短从 0 到 1；
2. 预热池（Warm Pool）维持可立即接管的实例。

Agent Sandbox 方案里，`SandboxWarmPool` 明确是通过维持预热 Sandbox Pod 来减少冷启动。这对交互式 Agent 非常有效，但多租户下不能给每个租户“全量热备”。

建议用分层热备而不是平均热备：

- Tier-0（核心租户）：固定 warm 实例 + 严格预算；
- Tier-1（普通租户）：按历史峰值分配 warm 上限；
- Tier-2（长尾租户）：冷启动 + 降级路由。

一个简单成本模型：

`WarmPoolCost ≈ Σ(tenant_warm_replicas × gpu_hour_price × time_window)`

把这个成本和“减少的超时损失/用户流失”一起算，预热池才有经营意义。

## 除了加速，还要减少“不必要冷启动”

这部分经常被忽略，但在生产里非常实用。

### 1) 用 VPA 降低冷启动后的资源抖动

当冷启动本身难以继续压缩时，可以用 VPA 把 Pod 资源更快拉回合理区间，减少刚恢复阶段因为资源不足导致的连锁抖动。建议先从 `Off` 或 `Initial` 模式做建议值观察，再逐步放开。

### 2) 用 Kubernetes v1.35 的“就地重启全部容器”

`RestartAllContainers`（v1.35 alpha）适用于“需要重跑 init 或重置状态，但不想整 Pod 重新调度”的场景。对于 AI 任务，这种方式往往比删除重建更快，尤其在大规模批处理和同步作业里价值明显。

### 3) 让就绪门禁表达“业务可服务”

把 `ModelLoaded/WarmupDone` 放进 `readinessGates`，避免实例在“容器 Ready 但模型未热”时提前接流量。这一点在混部和灰度发布中效果非常直接。

## 一份可执行的 30 天落地节奏

1. 第 1 周：补齐 6 段启动指标，产出模型分层冷启动预算。
2. 第 2 周：上线模型加载优化（Run:ai Streamer 或缓存编排）并 A/B。
3. 第 3 周：引入预热池分层策略，加入租户级成本看板。
4. 第 4 周：落地“减少重建”的变通路径（VPA + 就地重启）并固化发布门禁。

## 可连接到仓库的延伸阅读

- [GPU Pod 冷启动优化指南](../../kubernetes/gpu-pod-cold-start.md)
- [Pod 启动加速指南](../../kubernetes/pod-startup-speed.md)
- [推理模型生命周期管理](../../inference/model-lifecycle.md)
- [推理缓存体系](../../inference/caching.md)
- [调度优化与 Gang Scheduling](../../kubernetes/scheduling-optimization.md)
- [NVIDIA AICR 中文介绍](../2026-03-13/2026-03-13-nvidia-aicr-introduction_zh.md)
- [vLLM v0.18.0 AI-Infra 解读](../2026-03-24/2026-03-24-vllm-v0.18.0-ai-infra-highlights_zh.md)

## 参考

- CNCF:
  [The weight of AI models: Why infrastructure always arrives slowly](https://www.cncf.io/blog/2026/03/27/the-weight-of-ai-models-why-infrastructure-always-arrives-slowly/)
- Feisky:
  [当 Kubernetes 遇见 AI：云厂商如何为大模型训练重塑基础设施](https://feisky.xyz/posts/2025-12-04-kubernetes%E8%B6%85%E5%A4%A7%E8%A7%84%E6%A8%A1%E9%9B%86%E7%BE%A4%E4%BA%91%E5%8E%82%E5%95%86%E5%A6%82%E4%BD%95%E4%B8%BAai%E8%AE%AD%E7%BB%83%E9%87%8D%E5%A1%91%E5%9F%BA%E7%A1%80%E8%AE%BE%E6%96%BD/)
- GKE:
  [使用 Run:ai Model Streamer 加快 GKE 上的模型加载速度](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/run-ai-model-streamer?hl=zh-cn)
- Kubernetes:
  [在 Kubernetes 上使用 Agent Sandbox 运行智能体](https://kubernetes.io/zh-cn/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/)
- Kubernetes:
  [Kubernetes v1.35: New level of efficiency with in-place Pod restart](https://kubernetes.io/blog/2026/01/02/kubernetes-v1-35-restart-all-containers/)
- Kubernetes:
  [Vertical Pod Autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/vertical-pod-autoscale/)
- OneUptime:
  [How to Set Up GPU Workloads in Kubernetes for ML/AI](https://oneuptime.com/blog/post/2026-01-06-kubernetes-gpu-workloads-ml-ai/view)
- Fluid:
  [What is Fluid](https://fluid-cloudnative.github.io/docs)
- 字节跳动火山引擎（镜像分发加速参考）:
  [P2P 镜像加速方案](https://www.volcengine.com/docs/6460/658947?lang=zh)
- 社区实践（Serverless 视角）:
  [相关讨论](https://zhuanlan.zhihu.com/p/1987152570653905705)
