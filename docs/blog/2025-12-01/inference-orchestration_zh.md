---
status: Active
maintainer: pacoxu
date: 2025-12-01
tags: inference, orchestration, kubernetes, lws, pd-disaggregation, vllm
canonical_path: docs/blog/2025-12-01/inference-orchestration_zh.md
---

# 推理编排：当前解决方案与收敛趋势

**Note: 本文内容基于当前公开信息，仅用于技术参考。不同方案在实际效果上高度依赖具体业务场景、基础设施与生态集成情况。文中提到的架构归属与早期设计并不代表其未来走向，社区活跃度、开放度及长期演进才是更关键的判断因素。请结合自身场景作出选择。**

## 引言

2025 年，大型语言模型（LLM）开源推理编排领域发展迅速。多个项目涌现，旨在解决在
Kubernetes 上部署和扩展 LLM 推理工作负载的挑战，每个项目在工作负载管理、资源编排和
性能优化方面都有自己的方法。

本文概述当前的推理编排解决方案，分析生态系统的收敛趋势，并提出关于 Prefill-Decode
（PD）分离何时真正有价值的重要问题。

## 当前格局

### 快速发展，逐步收敛

推理编排领域的特点是：

- **多种实现**：多个项目解决类似问题
- **不同架构选择**：工作负载管理的不同方法
- **共同目标**：都旨在大规模优化 LLM 推理
- **涌现模式**：开始出现通用解决方案

尽管多样化，我们看到围绕关键模式的收敛：基于 LeaderWorkerSet（LWS）的架构、
智能路由和分离式服务模型。

## 工作负载编排解决方案

### 1. 双 LWS 架构

**[llm-d](https://github.com/llm-d/llm-d)** 实现了双 LeaderWorkerSet 架构用于
Prefill-Decode 分离：

- **两个 LWS 实例**：分别用于 prefill 和 decode worker
- **KServe 集成**：与 KServe 深度集成用于模型服务
- **LMCache 支持**：跨 worker 的高效 KV 缓存管理
- **路由 sidecar**：智能请求路由和缓存优化

```text
客户端 → 路由 Sidecar → Prefill LWS → KV 缓存 → Decode LWS → 响应
```

**为什么选择双 LWS？** 这种架构支持每个阶段的独立扩展和资源优化，同时通过
leader-worker 模式保持协调。

### 2. Serving Group：Volcano Kthena

**[Kthena](https://github.com/volcano-sh/kthena)** 采用不同的方法，引入
**Serving Group** 概念：

- **不使用双 LWS**：Kthena 有意避免双 LWS 模式
- **Gang 调度集成**：利用 Volcano 的 gang 调度能力
- **减少分层**：消除 StatefulSet/Pod 层的复杂性
- **直接集成**：与 Volcano 调度器原生集成

**为什么不用 LWS？** Kthena 团队发现，与 Volcano 的 gang 调度集成需要不同的架构。
双 LWS、StatefulSet 和 Pod 分层增加了复杂性，但在他们的用例中没有明显收益。

这个设计选择反映了一个关键洞察：**最佳编排解决方案取决于你现有的基础设施和调度
需求**。

> **更新 (v0.3.0)：** Kthena 自 v0.3.0 版本起已支持 LeaderWorkerSet 集成，
> 可根据工作负载需求灵活选择基于 LWS 或 Serving Group 的架构。

### 3. StormService：AIBrix

**[AIBrix StormService](https://github.com/vllm-project/aibrix)** 为 P/D 分离提供
专门的容器生命周期管理：

- **P/D 生命周期管理**：对 prefill 和 decode 容器的细粒度控制
- **多模式支持**：TP、PP、单 GPU 和 P/D 分离
- **StormService 和 RoleSet CRD**：用于 P/D 编排的自定义资源
- **企业级功能**：多租户、路由和可观测性

**架构：**

```text
AIBrix 控制平面
    ├── StormService 控制器
    │   ├── RoleSet (Prefill)
    │   └── RoleSet (Decode)
    ├── 网关和路由
    └── 自动扩缩容器
```

### 4. NVIDIA Dynamo：两种模式

**[Dynamo](https://github.com/ai-dynamo/dynamo)** 提供两种不同的部署模式：

**Grove 模式：**

- Kubernetes 编排的高性能推理
- NVIDIA 原生部署
- 为纯 NVIDIA 基础设施优化

**LWS 模式：**

- 使用 LeaderWorkerSet 的 Kubernetes 原生部署
- 多节点分离式服务
- 与 Kubernetes 生态系统集成

这种双模式方法允许用户根据基础设施选择合适的抽象级别。

### 5. SGLang RBG：LWS 启发

**[RBG（资源感知批处理调度器）](https://github.com/sgl-project/rbg)** 借鉴并复用了
LWS 的设计模式：

- **LWS 启发**：融入 LeaderWorkerSet 的成熟模式
- **资源感知调度**：基于资源优化批处理调度
- **批处理优化**：智能批处理策略提升吞吐量
- **P/D 支持**：支持分离的 prefill 和 decode 工作负载

## 收敛趋势

### 涌现的共同模式

尽管实现不同，几个模式正在收敛：

| 模式 | llm-d | Kthena | AIBrix | Dynamo | RBG |
| --- | --- | --- | --- | --- | --- |
| 基于 LWS | ✓ (双) | ✓ (v0.3.0+) | ✗ | ✓ (可选) | ✓ (启发) |
| P/D 分离 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 智能路由 | ✓ | ✓ | ✓ | ✓ | ✓ |
| KV 缓存管理 | LMCache | 原生 | 分布式 | 原生 | 原生 |

### 为什么有这么多实现？

多样性反映了不同的优化目标：

1. **调度集成**：Kthena 需要直接使用 Volcano gang 调度
2. **企业级功能**：AIBrix 专注于多租户和可观测性
3. **性能优先**：Dynamo 为 NVIDIA 硬件优化
4. **简单性**：RBG 提供轻量级的 LWS 启发方法
5. **生产就绪**：llm-d 展示完整的参考实现

## PD 分离的价值问题

### PD 分离是否总是有价值？

在 [KubeCon China 2025](https://www.bilibili.com/video/BV1dkUYBkEUc/) 上，袁宇文的
主题演讲《Kubernetes 为服务资源编排而生，MaaS 改变一切》提出了关于 PD 分离的
重要问题：

> "PD-分离角色调度 • 不太确定？（我们的答案是数据平面！）"

这挑战了 PD 分离总是有益的假设。

### PD 分离何时有帮助

PD 分离在以下情况下提供明确收益：

- **长 prefill，短 decode**：输入提示词比输出长得多
- **高并发**：需要同时服务大量请求
- **异构硬件**：不同阶段使用不同类型的 GPU
- **SLA 驱动调度**：不同的延迟要求（TTFT vs TPOT）

### PD 分离可能无益的情况

在以下情况下考虑替代方案：

- **短上下文**：prefill 和 decode 都很快
- **低并发**：同时请求数较少
- **同构硬件**：所有工作负载使用相同 GPU
- **复杂性成本**：运维开销超过收益
- **KV 缓存传输开销**：网络延迟超过计算节省

### 数据平面视角

"数据平面"的答案表明，PD 分离的价值取决于瓶颈实际存在的位置。在实施复杂编排
之前：

1. **分析你的工作负载**：了解时间花在哪里
2. **测量 KV 缓存传输成本**：网络开销很重要
3. **考虑更简单的替代方案**：不分离的 TP/DP
4. **评估运维复杂性**：更多组件 = 更多故障模式

## 配置优化：AIConfigurator

选择正确的 P/D 配置很复杂。NVIDIA 的
**[AIConfigurator](https://github.com/ai-dynamo/aiconfigurator)** 帮助优化
分离式部署配置：

### AIConfigurator 的功能

- **配置空间搜索**：评估数千种 P/D 组合
- **SLA 约束优化**：找到满足 TTFT/TPOT 目标的配置
- **硬件特定调优**：支持 H100、H200、B200，使用采集的数据
- **xPyD 规划**：确定最优的 prefill/decode worker 比例

### 使用示例

```bash
# 为 32 张 H200 GPU 上的 Qwen3-32B 找到最优配置
# SLA 目标：TTFT ≤ 300ms，TPOT ≤ 10ms
aiconfigurator cli default \
  --model QWEN3_32B \
  --total_gpus 32 \
  --system h200_sxm \
  --isl 4000 \
  --osl 500 \
  --ttft 300 \
  --tpot 10
```

### AIConfigurator 的重要性

传统自动扩缩（HPA/KPA）不理解 LLM 特有的特性。AIConfigurator 提供：

- **知情决策**：数据驱动的配置选择
- **预测性优化**：部署前估算性能
- **资源效率**：在 SLA 保证下最大化 GPU 利用率

## 建议

### 新部署

1. **从简单开始**：先使用单体服务（无 P/D 分离）
2. **先分析**：了解你的工作负载特性
3. **使用 AIConfigurator**：让数据指导配置决策
4. **逐步增加复杂性**：只有在收益明确时才引入 P/D

### 现有基础设施

| 如果你使用... | 考虑... |
| --- | --- |
| Volcano | Kthena（原生集成） |
| KServe | llm-d（深度集成） |
| vLLM | AIBrix（vLLM 生态系统） |
| NVIDIA GPU | Dynamo（NVIDIA 优化） |
| SGLang | RBG（LWS 启发，轻量级） |

### 采用 PD 分离前的关键问题

1. **你的 prefill 时间 >> decode 时间吗？** 如果不是，分离可能无益。
2. **你的网络能处理 KV 缓存传输吗？** 网络开销可能抵消收益。
3. **你需要独立扩展吗？** 如果 P 和 D 一起扩展，就让它们在一起。
4. **运维复杂性可接受吗？** 更多组件 = 更多故障模式。

## 总结

推理编排领域多样但正在收敛。关键要点：

- **存在多种解决方案**，因为不同基础设施有不同需求
- **基于 LWS 的模式很流行**，但不是通用的（Kthena 的 Serving Group 展示了替代
  方案）
- **PD 分离并非总是有价值** — 先分析你的工作负载
- **AIConfigurator 等工具帮助**导航复杂的配置空间
- **从简单开始，需要时再增加复杂性**，基于实际测量

未来可能会看到围绕成熟模式的进一步整合，但当前的多样性反映了快速发展领域的健康
实验。

---

## 参考资料

### 工作负载编排项目

- [llm-d](https://github.com/llm-d/llm-d) - P/D 的双 LWS 架构
- [Kthena](https://github.com/volcano-sh/kthena) - 基于 Volcano 的 Serving Group
- [AIBrix](https://github.com/vllm-project/aibrix) - P/D 的 StormService
- [Dynamo](https://github.com/ai-dynamo/dynamo) - NVIDIA 推理平台
- [RBG](https://github.com/sgl-project/rbg) - LWS 启发的批处理调度器

### 配置工具

- [AIConfigurator](https://github.com/ai-dynamo/aiconfigurator) - P/D 配置优化器

### 相关文档

- [PD 分离概述](../../inference/pd-disaggregation.md)
- [推理指南](../../inference/README.md)
- [LWS (LeaderWorkerSet)](https://github.com/kubernetes-sigs/lws)

### 演讲

- [KubeCon China 2025：Kubernetes 为服务资源编排而生，MaaS 改变一切](https://www.bilibili.com/video/BV1dkUYBkEUc/)
- [PDF 幻灯片](https://github.com/user-attachments/files/23845814/04-kubernetes-was-built-for-service-resource-orchestration.-maas-changes-everything-yu-wen-yuan-.pdf)

---

**作者**：AI 基础设施学习路径
**日期**：2025 年 12 月 1 日
**标签**：#inference #orchestration #kubernetes #lws #pd-disaggregation
