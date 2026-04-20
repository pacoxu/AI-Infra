---
status: Active
maintainer: pacoxu
date: 2026-04-15
tags: kubernetes, psi, cgroupv2, observability, ai-infrastructure, sre
canonical_path: docs/blog/2026-04-15/2026-04-15-kubernetes-v1.34-psi-metrics-beta-ai-infra_zh.md
source_urls:
  - https://github.com/kubernetes/website/pull/51574
  - https://github.com/kubernetes/enhancements/issues/4205
  - https://kubernetes.io/docs/reference/instrumentation/understand-psi-metrics/
  - https://docs.kernel.org/accounting/psi.html
---

# Kubernetes v1.34 PSI Metrics Beta：AI-Infra 该如何落地

`KEP-4205` 在 Kubernetes `v1.34` 进入 Beta 后，PSI（Pressure Stall
Information）不再只是 Linux 内核概念，而是可以直接进入 Kubernetes 节点/容器
观测与告警体系。

对 AI 平台而言，这件事的价值不是“多几个指标”，而是让我们能更早识别
**GPU 供给正常但 CPU/内存/IO 出现隐形拥塞** 的场景。

## 先说结论

要把 PSI 用起来，至少做三件事：

1. 在 Linux + cgroup v2 节点开启 `KubeletPSI` feature gate。
2. 接入 `/metrics/cadvisor` 暴露的新指标，并按节点/工作负载分组观察趋势。
3. 把 PSI 告警接入扩缩容或调度策略，而不是只做 dashboard 展示。

## Upstream PR 里最值得关注的点

来自 `kubernetes/website#51574` 的关键信息：

- `v1.34` 中 PSI metrics 升级到 Beta。
- kubelet 可通过两条链路暴露 PSI：Summary API 与 `/metrics/cadvisor`。
- 新增六个核心指标：
  - `container_pressure_cpu_stalled_seconds_total`
  - `container_pressure_cpu_waiting_seconds_total`
  - `container_pressure_memory_stalled_seconds_total`
  - `container_pressure_memory_waiting_seconds_total`
  - `container_pressure_io_stalled_seconds_total`
  - `container_pressure_io_waiting_seconds_total`
- 依赖前提：Linux kernel `>=4.20` 且使用 cgroup v2。
- Windows 节点不提供 PSI 指标。

## 为什么 AI 场景更需要 PSI

在推理和训练集群中，常见问题不是资源“用满”而是资源“争用”导致延迟抖动：

- Token 生成延迟突然上升，但 GPU 利用率仍高且稳定。
- KV cache 命中率没有明显下降，但 p99 延迟持续拉长。
- 作业吞吐下降，却看不到明显 OOM 或 CPU limit 触顶。

这类问题用传统 utilization 指标很难提前发现。PSI 的 `some/full` 能更快反映
“任务在等资源”的时间比例。

## 最小落地步骤

### 1) 开启 feature gate

在 kubelet 启动参数中开启：

```bash
--feature-gates=KubeletPSI=true
```

### 2) 采集与记录

- Prometheus 抓取 `kubelet /metrics/cadvisor`
- 保留 `pod`、`namespace`、`node`、`container` 标签
- 对训练队列与在线推理服务分开看板

### 3) 告警与动作联动

建议先从两类告警开始：

- **Node 级持续压力**：`memory full` 或 `io full` 连续上升
- **Workload 级异常抖动**：同一 deployment 中 PSI 分布突然分化

示例（仅示意）：

```promql
rate(container_pressure_memory_stalled_seconds_total{container!=""}[5m]) > 0.2
```

```promql
rate(container_pressure_io_waiting_seconds_total{container!=""}[5m]) > 0.15
```

## 和现有 AI-Infra 能力怎么结合

1. 与调度结合：把高 PSI 节点作为低优先级放置候选。
2. 与弹性结合：当 PSI 持续偏高而 GPU 未饱和时，优先扩 CPU/内存侧资源。
3. 与容量规划结合：按业务线比较 PSI 热点节点，识别“伪充足容量”。

## 一份可执行的两周计划

1. 第 1-2 天：确认所有 Linux 节点已切到 cgroup v2。
2. 第 3-4 天：灰度开启 `KubeletPSI`，验证指标入库完整性。
3. 第 5-7 天：建立 Node/Pod 双视角 PSI 看板。
4. 第 8-10 天：配置两条基础告警并做一次演练。
5. 第 11-14 天：把 PSI 信号接入调度或扩容策略，形成闭环。

## 参考

- Kubernetes Website PR:
  [Add blog post for PSI Metrics graduate to Beta](https://github.com/kubernetes/website/pull/51574)
- KEP Issue: [KEP-4205](https://github.com/kubernetes/enhancements/issues/4205)
- Kubernetes Docs:
  [Understand PSI Metrics](https://kubernetes.io/docs/reference/instrumentation/understand-psi-metrics/)
- Linux Kernel Docs: [PSI](https://docs.kernel.org/accounting/psi.html)
