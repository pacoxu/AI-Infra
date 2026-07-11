---
status: Active
maintainer: pacoxu
last_updated: 2026-07-10
tags: kubernetes, tas, topology-aware-scheduling, kueue, dra, workload-api
canonical_path: docs/kubernetes/tas-validation.md
source_urls:
  - https://api.github.com/repos/pacoxu/AI-Infra/issues/362
  - https://api.github.com/repos/pacoxu/AI-Infra/issues/297
  - https://api.github.com/repos/pacoxu/AI-Infra/issues/285
  - https://api.github.com/repos/pacoxu/AI-Infra/issues/359
  - https://api.github.com/repos/kubernetes/enhancements/issues/5732
  - https://kueue.sigs.k8s.io/docs/concepts/topology_aware_scheduling/
  - https://raw.githubusercontent.com/kai-scheduler/KAI-Scheduler/main/docs/topology/README.md
  - https://raw.githubusercontent.com/volcano-sh/volcano/master/docs/user-guide/how_to_use_network_topology_aware_scheduling.md
  - https://api.github.com/repos/koordinator-sh/koordinator/contents/docs/proposals/scheduling/20250611-networktopology-aware-scheduling.md?ref=main
---

# TAS 验证报告：Topology Aware Scheduling 是否值得进入主线

本文沉淀 issue
[#362](https://api.github.com/repos/pacoxu/AI-Infra/issues/362)
的验证设计、实验清单、策略对照表和阶段性结论。事实状态核对到
**2026-07-10**。

这不是一份声称已经完成真实 GPU/RDMA 集群压测的 benchmark。当前仓库没有绑定可用的
GPU/NIC 拓扑测试集群，因此本文把交付物拆成两层：

- **已完成**：验证范围、A/B 实验清单、指标口径、配置样例、风险与决策门槛。
- **待真实集群执行**：训练与推理 workload 的有/无 TAS 对照数据采集。

## 一页结论

`TAS` 值得进入下一阶段 PoC，但不应该直接作为默认调度策略上线。

推荐路线是：

1. **近期主验证路径：Kueue TAS**。它已经覆盖 queue / admission / quota 语义，
   `TopologyAwareScheduling` 是 Kueue 默认开启的 beta 能力，最适合回答
   “拓扑收益是否会被 queue wait 和 pending 行为抵消”。
2. **中期跟进路径：Kubernetes 原生 WAS / PodGroup / TAS**。KEP-5732 在
   v1.36 进入 alpha，当前 KEP 状态把 beta 目标放在 v1.37；它更适合作为
   主线收敛方向，而不是立即替代 Kueue。
3. **对照路径：KAI / Volcano / Koordinator**。这些调度器在 gang、拓扑、
   分层队列或 GPU 场景上更激进，但会引入第二调度器和生态绑定成本，适合作为
   能力上限验证，不适合作为当前仓库的默认优先路径。

进入下一阶段的条件：

- 训练场景里，`TAS` 至少让 cross-domain traffic 或通信热点明显下降，并且
  job completion time 有可解释改善。
- 推理或 `GPU + NIC` 强绑定场景里，`TAS` 至少降低 TTFT / startup latency
  尾部波动，或减少跨 rack / 跨 block 的 RDMA 路径。
- `TAS` 带来的 queue wait、pending、head-of-line blocking 增幅可控。
- 失败原因能被事件、Workload 状态、scheduler / Kueue 指标解释。

不进入下一阶段的条件：

- 只在少数满配训练任务中有效，普通混部和推理场景收益不稳定。
- required topology 造成大量长时间 pending，且只能靠人工回退。
- 现有 queue / quota / fairness 模型无法解释谁被阻塞、为什么被阻塞。
- 需要强绑定某个非主线调度器，且无法复用 DRA / Kueue / WAS 的上游路径。

## 需要回答的问题

### 哪些 workload 对拓扑敏感

| Workload | 敏感维度 | TAS 价值 | 备注 |
| --- | --- | --- | --- |
| 多机分布式训练 | rack / block / IB / RoCE / NVLink domain | 高 | AllReduce、AllGather、pipeline stage 间通信会放大拓扑差异。 |
| `GPU + NIC` 强绑定任务 | PCIe root / NUMA / RDMA fabric | 高 | 重点是同 NUMA、同 PCIe root、GPU Direct RDMA 可用性。 |
| P/D 分离推理 | prefill / decode role 之间的 rack / block | 中到高 | 需要先确认 role 间流量是否成为瓶颈。 |
| MoE 或专家并行推理 | expert / router / all-to-all 通信域 | 中到高 | 更适合 segment 或 subgroup 级 topology，而不是简单全组同 rack。 |
| 单 Pod 推理副本 | NUMA / GPU / NIC locality | 中 | 通常用 Pod-level DRA / Topology Manager 即可。 |
| 离线 ETL / CPU batch | zone / failure domain | 低 | 更适合普通 spread / binpack / quota 策略。 |

### Pod-level 与 Workload-level 拓扑约束

| 层次 | 适用场景 | 推荐机制 | 不适合场景 |
| --- | --- | --- | --- |
| Pod-level | 单 Pod 内 GPU、NIC、CPU、memory 的局部性 | DRA、Topology Manager、node affinity | 多 Pod 之间必须同 rack 或同 block 的训练任务。 |
| PodSet / Workload-level | 一组 Pod 需要作为整体选择 topology domain | Kueue TAS、Kubernetes WAS TAS、KAI / Volcano gang topology | 单副本服务、没有强通信关系的普通 batch。 |
| Subgroup / segment-level | DP / PP / TP、prefill / decode、router / expert 分组 | KAI segment、Volcano partition、Koordinator GangGroup 方向 | 所有 Pod 完全同构且只需要简单同 rack 的任务。 |

判断规则：

- **单 Pod 内部资源绑定**：优先 Pod-level。
- **多个 Pod 必须整体启动且通信密集**：优先 Workload-level。
- **组内还分角色、分 pipeline 或分 parallel group**：需要 subgroup / segment 语义。

## 上游能力状态

| 路径 | 当前信号 | 适合验证的问题 | 风险 |
| --- | --- | --- | --- |
| Kueue TAS | `TopologyAwareScheduling` beta，默认开启；支持 Topology、ResourceFlavor、PodSet annotations、多层拓扑和 failed node replacement。 | queue / admission / topology 的组合收益。 | Kueue 需要维护全量 Pods / Nodes 拓扑缓存，会增加内存和调度耗时。 |
| Kubernetes WAS TAS | KEP-5732：v1.36 alpha，v1.37 beta 目标；引入 PodGroup topology constraints 和 placement 插件扩展点。 | 原生 kube-scheduler 是否能承载 Workload-level placement。 | 当前不是 queue / fairness / quota 系统，仍需 Kueue 或上层队列。 |
| KAI Scheduler | 有 KAI Topology CRD、required / preferred placement、多层拓扑和 segment placement。 | GPU 训练、层级 gang、分段拓扑的能力上限。 | 需要引入 KAI 调度栈和对应 PodGroup / queue 语义。 |
| Volcano | HyperNode 表达网络拓扑；支持 hard / soft network topology、partitionPolicy 和 HyperNode binpack。 | 网络拓扑与 subgroup partition 的训练场景。 | 第二调度器和 Volcano Job 绑定成本较高。 |
| Koordinator | 提出 ClusterNetworkTopology、GangGroup、parallel model、job-level preemption 的网络拓扑方案。 | quota、preemption、topology 组合的高级场景。 | 更偏 proposal / 特定生态路径，需额外确认实现成熟度。 |

## 验证策略

本验证不追求一次性比较所有调度器。核心问题是：

> 在当前平台主线中，启用 topology-aware placement 的收益是否大于它带来的
> queue wait、pending、碎片化和运维复杂度。

因此实验分三组：

1. **Kueue TAS A/B**：验证 queue / admission / topology 的主路径。
2. **Pod-level DRA / Topology Manager A/B**：验证 `GPU + NIC + NUMA` 绑定是否足够。
3. **生态对照**：只在 Kueue 无法表达 subgroup / segment 时验证 KAI、Volcano 或
   Koordinator。

## 通用环境前提

真实执行时需要一个单集群 staging 环境：

- Kubernetes 版本：优先使用与 #285 基线一致的版本；如果验证原生 WAS TAS，需要
  同步部署支持 KEP-5732 的版本和 feature gates。
- Kueue：安装启用 `TopologyAwareScheduling` 的版本。
- GPU：至少 2 个 rack / block，每个 domain 至少 2 个 GPU 节点。
- 网络：至少能区分同 rack、跨 rack、跨 block 的路径。
- 观测：Prometheus、DCGM exporter、Kueue metrics、scheduler metrics、Pod events。
- DRA：如验证 `GPU + NIC`，需要对应 DRA driver 或等价设备分配路径。

建议拓扑标签：

```yaml
topology.kubernetes.io/zone: "zone-a"
topology.aiinfra.dev/block: "block-a"
topology.aiinfra.dev/rack: "rack-a1"
kubernetes.io/hostname: "gpu-node-a1-01"
network.topology.nvidia.com/block: "s1"
network.topology.nvidia.com/spine: "s2"
gpu.aiinfra.dev/nvlink-domain: "nvl-0"
```

## Kueue TAS 最小配置样例

以下样例用于说明验证结构。实际执行前必须按安装的 Kueue 版本校验 `apiVersion`
和字段名。

```yaml
apiVersion: kueue.x-k8s.io/v1alpha1
kind: Topology
metadata:
  name: gpu-rack-topology
spec:
  levels:
  - nodeLabel: topology.aiinfra.dev/block
  - nodeLabel: topology.aiinfra.dev/rack
  - nodeLabel: kubernetes.io/hostname
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata:
  name: gpu-a100-tas
spec:
  nodeLabels:
    aiinfra.dev/gpu-type: a100
  topologyName: gpu-rack-topology
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: ai-gpu
spec:
  namespaceSelector: {}
  resourceGroups:
  - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
    flavors:
    - name: gpu-a100-tas
      resources:
      - name: cpu
        nominalQuota: 1024
      - name: memory
        nominalQuota: 4Ti
      - name: nvidia.com/gpu
        nominalQuota: 64
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata:
  namespace: ai-bench
  name: tas
spec:
  clusterQueue: ai-gpu
```

用户侧 required rack placement：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  namespace: ai-bench
  name: train-required-rack
  labels:
    kueue.x-k8s.io/queue-name: tas
spec:
  parallelism: 8
  completions: 8
  template:
    metadata:
      annotations:
        kueue.x-k8s.io/podset-required-topology: topology.aiinfra.dev/rack
    spec:
      restartPolicy: Never
      containers:
      - name: train
        image: nvcr.io/nvidia/pytorch:25.04-py3
        command: ["bash", "-lc", "sleep 3600"]
        resources:
          limits:
            nvidia.com/gpu: "1"
          requests:
            cpu: "8"
            memory: 64Gi
            nvidia.com/gpu: "1"
```

用户侧 preferred rack placement：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  namespace: ai-bench
  name: train-preferred-rack
  labels:
    kueue.x-k8s.io/queue-name: tas
spec:
  parallelism: 8
  completions: 8
  template:
    metadata:
      annotations:
        kueue.x-k8s.io/podset-preferred-topology: topology.aiinfra.dev/rack
    spec:
      restartPolicy: Never
      containers:
      - name: train
        image: nvcr.io/nvidia/pytorch:25.04-py3
        command: ["bash", "-lc", "sleep 3600"]
        resources:
          limits:
            nvidia.com/gpu: "1"
          requests:
            cpu: "8"
            memory: 64Gi
            nvidia.com/gpu: "1"
```

## 实验 1：分布式训练 A/B

目标：验证同 rack / 同 block placement 对训练通信和完成时间的影响。

Workload：

- 8 Pod 或 16 Pod distributed training。
- 每 Pod 1 GPU。
- 训练脚本优先选择能稳定产生 AllReduce / AllGather 的小模型压测。
- 同一镜像、同一数据集、同一 batch size，避免把模型变量混入调度实验。

A/B 设计：

| 组别 | 约束 | 预期观察 |
| --- | --- | --- |
| A0 baseline | 不声明 TAS，仅使用 queue 和 GPU request | 可能跨 rack / block，queue wait 更短。 |
| A1 preferred | `podset-preferred-topology=rack` | 如果 rack 容量足够，应减少跨域流量且不显著增加 pending。 |
| A2 required | `podset-required-topology=rack` | 最能降低跨 rack，但最容易放大 head-of-line blocking。 |
| A3 block required | required block + rack preferred | 适合单 rack 不足但 block 内网络仍优于跨 block 的情况。 |

采集指标：

```text
queue_wait_seconds = Workload QuotaReserved time - Workload created time
admission_latency_seconds = Workload admitted time - Workload created time
scheduling_latency_seconds = last PodScheduled time - first Pod created time
startup_latency_seconds = all workers ready time - Workload admitted time
jct_seconds = job completion time - Workload created time
cross_domain_edges = count(worker pairs where rack/block differs)
gpu_utilization_avg = avg(DCGM_FI_DEV_GPU_UTIL)
gpu_idle_before_start = sum(GPU allocated but training not started)
```

判定门槛：

- 进入下一阶段：A1 或 A3 在 JCT、通信耗时或跨域流量上有稳定改善，且 P95
  queue wait 增幅不超过 15%。
- 谨慎推进：A2 改善训练耗时，但 P95 queue wait 增幅超过 30%。
- 不推进：只有 required rack 有收益，而 preferred / block required 无法提供稳定改善。

结果记录模板：

| Run | 组别 | Pods | 拓扑落点 | Queue wait P50/P95 | JCT P50/P95 | 跨 rack 边数 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | A0 | 8 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |
| T2 | A1 | 8 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |
| T3 | A2 | 8 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |
| T4 | A3 | 8 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |

## 实验 2：拆角色推理或 GPU + NIC 强绑定 A/B

目标：验证 topology placement 对推理启动、TTFT、跨域调用和 `GPU + NIC` 绑定的影响。

Workload 二选一：

- P/D 分离推理：prefill 与 decode 分成不同 PodSet。
- `GPU + NIC` 强绑定任务：每个 Pod 需要 1 GPU 和 1 RDMA NIC。

A/B 设计：

| 组别 | 约束 | 预期观察 |
| --- | --- | --- |
| B0 baseline | 无 TAS，只做普通 queue admission | role 可能跨 rack；GPU/NIC 可能落在非最佳路径。 |
| B1 Pod-level | DRA / Topology Manager 约束 GPU + NIC | 验证单 Pod 内绑定是否已经足够。 |
| B2 Workload-level | role 同 rack 或同 block | 验证 role 间通信是否明显受拓扑影响。 |
| B3 subgroup | prefill / decode 分组 placement | 如果 B2 太粗，进一步看 subgroup 是否必要。 |

采集指标：

```text
admission_latency_seconds
pod_scheduled_to_ready_seconds
ttft_p50_p95
tpot_p50_p95
request_success_rate
prefill_decode_cross_rack_calls
rdma_path_locality
gpu_nic_same_numa_ratio
```

判定门槛：

- 如果 B1 已经解决主要波动，先把主线聚焦在 DRA / Topology Manager，不升级到
  Workload-level TAS。
- 如果 B2 明显改善 TTFT / TPOT 或跨 rack calls，推理场景继续验证 Kueue TAS。
- 如果只有 B3 有效果，说明需要 subgroup / segment 语义，进入 KAI、Volcano 或
  Koordinator 对照验证。

结果记录模板：

| Run | 组别 | Workload | TTFT P50/P95 | Startup P95 | 跨 rack calls | GPU/NIC 同域率 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| I1 | B0 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |
| I2 | B1 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |
| I3 | B2 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |
| I4 | B3 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |

## 实验 3：pending 与碎片化压力

目标：验证 TAS 是否显著放大 head-of-line blocking、资源碎片化或不可解释 pending。

场景：

1. 先提交一批小 GPU jobs，制造 rack 内碎片。
2. 再提交一个 required rack 的 8-GPU training job。
3. 对比 required、preferred、无 TAS 的 admission 和 pending 行为。
4. 释放一个 rack 内小 job，观察 required job 是否能恢复。

关键问题：

- required rack 是否因为碎片长期 pending。
- preferred rack 是否能在 fallback 后保持可接受性能。
- Kueue event / Workload status 是否能解释缺少哪个 topology domain。
- 抢占或回收是否扩大到不该被打断的队列。

结果记录模板：

| Case | 约束 | 初始碎片 | Pending 时长 | 恢复条件 | 受影响队列 | 是否可解释 |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | 无 TAS | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |
| P2 | preferred rack | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |
| P3 | required rack | 待采集 | 待采集 | 待采集 | 待采集 | 待采集 |

## 指标与查询入口

Kueue / scheduler：

```promql
workqueue_depth{name=~".*kueue.*"}
kueue_admitted_workloads_total
kueue_pending_workloads
kueue_evicted_workloads_total
scheduler_pending_pods
scheduler_schedule_attempts_total
scheduler_scheduling_duration_seconds
```

Kubernetes 原生 WAS TAS beta 目标指标：

```promql
scheduler_placement_total
scheduler_placement_evaluations_total
scheduler_placement_evaluation_duration_seconds
```

GPU / network：

```promql
DCGM_FI_DEV_GPU_UTIL
DCGM_FI_DEV_FB_USED
DCGM_FI_DEV_PCIE_TX_BYTES
DCGM_FI_DEV_PCIE_RX_BYTES
DCGM_FI_PROF_NVLINK_TX_BYTES
DCGM_FI_PROF_NVLINK_RX_BYTES
```

事件与对象：

```shell
kubectl get workloads -A
kubectl describe workload -n ai-bench <name>
kubectl get pods -n ai-bench -owide
kubectl get events -n ai-bench --sort-by=.lastTimestamp
kubectl get nodes -L topology.aiinfra.dev/block,topology.aiinfra.dev/rack
```

## 拓扑策略对照表

| 策略 | 约束 | 收益 | 代价 | 适用场景 | 回退条件 |
| --- | --- | --- | --- | --- | --- |
| 无 TAS | 只看资源和普通 affinity | queue wait 最短、吞吐高 | 训练通信和推理跨域不可控 | 默认 baseline | 通信或 TTFT 波动明显时升级。 |
| Preferred rack | 尽量同 rack，不满足可上浮 | 收益和 pending 风险平衡 | 不保证最优拓扑 | 大多数训练 / 推理灰度 | 收益不稳定或 fallback 过多。 |
| Required rack | 必须同 rack | 最大限度减少跨 rack | 最容易 pending 和阻塞队头 | 小到中等规模、rack 容量确定的训练 | P95 queue wait 增幅 > 30%。 |
| Required block + preferred rack | block 内收敛，rack 内尽量收敛 | 比 required rack 更稳 | 跨 rack 仍可能存在 | 单 rack 容量不足的大训练 | block 内通信仍是瓶颈。 |
| Pod-level GPU + NIC | 同 NUMA / PCIe / NIC | 单 Pod 延迟和 RDMA 稳定 | 不解决多 Pod 同域 | 单副本推理、GPU Direct RDMA | role 间跨域成为瓶颈。 |
| Subgroup / segment | 每个子组独立拓扑约束 | 支持 DP / PP / P-D 分组 | API 和调度器复杂度高 | MoE、PP/DP、P-D 解耦推理 | 当前 workload 无清晰子组。 |

## 实现路径建议

### 立即执行

1. 用 Kueue TAS 跑实验 1 和实验 2。
2. 先使用 preferred rack / block，不把 required rack 作为默认策略。
3. 对所有实验同时记录 queue wait、pending reason、JCT / TTFT 和拓扑落点。
4. 用无 TAS、preferred、required 三组结果判断收益是否真实。

### 暂缓执行

- 不直接切到 KAI / Volcano / Koordinator 作为主线调度器。
- 不把 `required rack` 放进默认模板。
- 不在缺少真实 topology metrics 的情况下宣称 TAS 有确定性收益。

### 下一阶段 Owner 输入

如果真实 A/B 数据满足进入条件，建议为 #297 拆出后续任务：

- Kueue TAS PoC 结果归档。
- DRA `GPU + NIC` Pod-level 约束验证。
- Kubernetes WAS TAS v1.37+ 跟踪与差异分析。
- Subgroup / segment topology 需求是否进入 #359 的层级 PodGroup 研究。

## 未决风险

1. **拓扑源可信度**：node labels、Topograph、CMDB、交换机拓扑发现之间必须有一致来源。
2. **调度可解释性**：required topology pending 需要能定位是 quota、domain 容量还是普通 filter。
3. **容量规划**：rack/block 容量不足时，TAS 会把资源短缺从“全局不足”变成“域内不足”。
4. **碎片化**：强 co-location 可能提升单个 job 性能，但降低集群整体可用组合。
5. **混部影响**：推理服务不能为了训练任务的 required rack 被长时间挤压。
6. **版本漂移**：Kueue、DRA、WAS 的 API 和 feature gate 仍在快速演进，需要按版本锁定样例。

## 当前验收状态

| 验收项 | 状态 | 说明 |
| --- | --- | --- |
| 覆盖 2 类拓扑敏感 workload | 已完成设计 | 分布式训练、拆角色推理 / `GPU + NIC` 强绑定。 |
| 有 / 无 TAS 对照结果 | 待执行 | 本地没有目标集群，未伪造 benchmark。 |
| 收益、回退条件、不适用场景 | 已完成 | 见策略对照表和判定门槛。 |
| 为 #297 提供是否继续 TAS 的结论 | 部分完成 | 建议进入 Kueue TAS PoC，不建议直接生产默认启用。 |

## 参考资料

- [#362 TAS 验证](https://api.github.com/repos/pacoxu/AI-Infra/issues/362)
- [#297 平台内核线：资源编排与一致性](https://api.github.com/repos/pacoxu/AI-Infra/issues/297)
- [#285 DRA + Kueue 基线 PoC](https://api.github.com/repos/pacoxu/AI-Infra/issues/285)
- [#359 Composite / Sub PodGroup 调度模型](https://api.github.com/repos/pacoxu/AI-Infra/issues/359)
- [KEP-5732 Topology-aware workload scheduling](https://api.github.com/repos/kubernetes/enhancements/issues/5732)
- [Kueue Topology Aware Scheduling](https://kueue.sigs.k8s.io/docs/concepts/topology_aware_scheduling/)
- [KAI Scheduler Topology Aware Scheduling](https://raw.githubusercontent.com/kai-scheduler/KAI-Scheduler/main/docs/topology/README.md)
- [Volcano Network Topology Aware Scheduling](https://raw.githubusercontent.com/volcano-sh/volcano/master/docs/user-guide/how_to_use_network_topology_aware_scheduling.md)
- [Koordinator topology proposal](https://api.github.com/repos/koordinator-sh/koordinator/contents/docs/proposals/scheduling/20250611-networktopology-aware-scheduling.md?ref=main)
