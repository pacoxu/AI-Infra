---
status: Active
maintainer: pacoxu
date: 2026-04-01
tags: kubernetes, kubelet, swap, memory-pressure, sig-node, eviction, scheduling
canonical_path: docs/blog/2026-04-01/2026-04-01-kubernetes-swap-status-kubelet-memory-pressure_zh.md
source_urls:
  - https://github.com/kubernetes/enhancements/issues/2400
  - https://github.com/kubernetes/enhancements/issues/5359
  - https://github.com/kubernetes/enhancements/issues/5424
  - https://github.com/kubernetes/enhancements/issues/5433
  - https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2400-node-swap
  - https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/
  - https://kubernetes.io/docs/reference/node/swap-behavior/
  - https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/
  - https://kubernetes.io/blog/2023/08/24/swap-linux-beta/
  - https://kubernetes.io/blog/2025/03/25/swap-linux-improvements/
  - https://kubernetes.io/blog/2025/08/19/tuning-linux-swap-for-kubernetes-a-deep-dive/
  - https://www.youtube.com/watch?v=bFrEPfls5PQ
  - https://www.youtube.com/watch?v=El94Z0JowF0
---

# Kubernetes Swap 现状（2026）：kubelet 行为、内存压力与场景化落地

这篇文章聚焦 Kubernetes 中 swap 的当前状态，重点围绕 `KEP-2400`、kubelet 当前行为边界，以及在不同业务场景下如何落地。

文中状态信息核对时间为 **2026-04-01**。

## 先说结论

- `KEP-2400`（Node memory swap support）已经完成：
  - issue `#2400` 已关闭（**2025-09-17**）。
  - KEP 状态为 `implemented`，阶段 `stable`，里程碑 `v1.34`。
- `NodeSwap` 在 Feature Gates 页面中已经标记为 **1.34 GA**。
- kubelet 当前默认策略是“保守可控”：
  - 默认 `NoSwap`，可选 `LimitedSwap`；
  - 工作负载 swap 路径依赖 Linux + cgroup v2。
- 下一阶段重点不是“能不能开 swap”，而是“是否具备工作负载级可控能力”：
  - `#5359` workload controlled swap
  - `#5424` swap-aware scheduling
  - `#5433` swap-aware evictions

## 1. 当前状态快照

### 1.1 KEP-2400

- Issue: [kubernetes/enhancements#2400](https://github.com/kubernetes/enhancements/issues/2400)
- 标题: `Node memory swap support`
- 状态: `CLOSED`
- 关闭时间: **2025-09-17**
- 标签: `sig/node`, `stage/stable`
- 里程碑: `v1.34`

### 1.2 仍在推进的三条后续线

- [#5359 Workload Controlled Swap](https://github.com/kubernetes/enhancements/issues/5359)
  - `OPEN`，当前仍是 alpha 早期推进态
- [#5424 Swap-Aware Scheduling](https://github.com/kubernetes/enhancements/issues/5424)
  - `OPEN`，目前内容仍偏占位
- [#5433 Swap-Aware Evictions](https://github.com/kubernetes/enhancements/issues/5433)
  - `OPEN`，目前内容仍偏占位

## 2. kubelet 现在到底怎么工作

对 Linux 节点，核心开关主要有两个：

1. `failSwapOn`
2. `memorySwap.swapBehavior`

示例（允许 kubelet 在有 swap 的节点启动，但默认不给 workload 用）：

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
failSwapOn: false
memorySwap:
  swapBehavior: NoSwap
```

可选行为：

- `NoSwap`（默认）: Kubernetes 管理的 workload 不使用 swap。
- `LimitedSwap`: workload 在规则约束下可使用 swap。

在 `LimitedSwap` 下，容器 swap 上限按请求占比自动计算：

```text
containerSwapLimit = (containerMemoryRequest / nodeTotalMemory) * totalPodsSwapAvailable
```

这也是为什么 `KEP-2400` 解决的是“节点级基础能力”，而不是“完整工作负载级策略控制”。

## 3. 场景化落地（结合两份 KubeCon slides）

下面把“是否该开 swap”拆成更具体的 4 类场景。

### 场景 A：成本/密度导向的离线或弱实时池

典型特征：

- 业务常见“内存 request 偏保守”，但活跃工作集并不一直顶满；
- 对 tail latency 不极致敏感；
- 更关心单位节点承载和资源成本。

对应到 `Swap Smart, Save Big`（KubeCon EU 2024）的核心观点：

- 同样物理内存下，通过回收“低活跃页”有机会提升承载密度。
- 实际价值来自“减少过度 request 带来的空转内存”。

落地建议：

- 先在专用 worker pool 试点 `LimitedSwap`，不要全局一键开启。
- swap 盘优先 SSD/NVMe，尽量与业务 I/O 隔离。
- 对该池做容量收益与延迟退化的双指标评估。

### 场景 B：内存突刺导致 OOMKill 先于 Eviction

典型特征：

- 节点在压力突刺时出现 `OOMKilled`；
- kubelet eviction 来不及触发或触发太晚；
- 表现为“偶发雪崩、恢复慢”。

对应 `Deep Dive: Handling Kubernetes Memory Pressure...`（KubeCon NA 2025）与官方调优博客的核心经验：

- 只开 swap 不够，必须配套内核回收参数与 eviction 阈值。
- `vm.min_free_kbytes`、`vm.watermark_scale_factor` 决定 reclaim “提前量”和“跑道长度”。

落地建议：

- 先把内核回收窗口调到可观测可控，再调整 kubelet eviction 阈值。
- 重点观察 OOM 与 Evicted 的比例变化，而不是只看 swap 使用率。
- 压测覆盖“渐进负载 + 突刺负载”两种模式。

### 场景 C：控制面与系统关键组件保护

典型特征：

- 控制面和系统守护进程稳定性优先级极高；
- 不能接受 swap 带来的随机 I/O 抖动。

官方文档和两份 slides 都强调：

- 控制面节点建议保持保守（通常不启用 workload swap）。
- 系统关键进程要避免被 swap 和 I/O 争抢拖慢。

落地建议：

- 系统关键 daemons（如 kubelet/container runtime）设置更严格保护。
- 提升 system slice I/O 优先级，避免 swap I/O 抢占关键路径。
- 把 swap 策略与节点角色绑定，不要同一模板覆盖所有节点。

### 场景 D：需要更细粒度控制（容器/进程级）

典型特征：

- 你希望做到 QoS 之外的细粒度策略，例如按容器、按进程、按空闲时长控制 pageout。

EU 2024 slides 的结论是：

- 社区已有 NRI + memtierd 等 out-of-tree 方案可实验；
- 但 upstream 原生能力仍在演进，尚未形成统一稳定 API。

落地建议：

- 生产主路径先用 upstream 已稳定能力；
- 细粒度策略先在实验池验证，再决定是否平台化。

## 4. 可观测与验证清单

至少覆盖以下信号：

- kubelet `/metrics/resource`:
  - `node_swap_usage_bytes`
  - `container_swap_usage_bytes`
  - `container_swap_limit_bytes`
- kubelet `/stats/summary`
- `kubectl top --show-swap`
- node status swap capacity

常用命令：

```bash
kubectl top nodes --show-swap
kubectl top pods -A --show-swap
kubectl get nodes -o go-template='{{range .items}}{{.metadata.name}}: {{if .status.nodeInfo.swap.capacity}}{{.status.nodeInfo.swap.capacity}}{{else}}<unknown>{{end}}{{"\n"}}{{end}}'
```

## 5. 建议的推进顺序（2026）

1. 从 `NoSwap + failSwapOn: false` 起步，先验证节点级稳定性。
2. 仅在目标池灰度 `LimitedSwap`，并绑定明确业务场景。
3. 同步调优内核 reclaim 参数与 kubelet eviction 阈值。
4. 以“稳定性 + 成本收益”双指标决定是否扩面。
5. 关注 `#5359/#5424/#5433` 进展，预留后续策略升级空间。

## 参考

- [KEP-2400 Issue](https://github.com/kubernetes/enhancements/issues/2400)
- [KEP-2400 Design](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2400-node-swap)
- [Swap memory management docs](https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/)
- [Linux Node Swap Behaviors](https://kubernetes.io/docs/reference/node/swap-behavior/)
- [Feature Gates: NodeSwap](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)
- [Kubernetes 1.28: swap beta](https://kubernetes.io/blog/2023/08/24/swap-linux-beta/)
- [Fresh Swap Features for Linux Users in Kubernetes 1.32](https://kubernetes.io/blog/2025/03/25/swap-linux-improvements/)
- [Tuning Linux Swap for Kubernetes: A Deep Dive](https://kubernetes.io/blog/2025/08/19/tuning-linux-swap-for-kubernetes-a-deep-dive/)
- [Deep Dive: Handling Kubernetes Memory Pressure & Achieving Workload Stability With Swap](https://www.youtube.com/watch?v=bFrEPfls5PQ)
- [Swap Smart, Save Big](https://www.youtube.com/watch?v=El94Z0JowF0)
