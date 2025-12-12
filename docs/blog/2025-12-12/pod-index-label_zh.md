---
status: Active
maintainer: pacoxu
date: 2025-12-12
tags: kubernetes, kep-4017, pod-index-label, co-evolving, statefulset, indexed-jobs, lws
canonical_path: docs/blog/2025-12-12/pod-index-label_zh.md
---

# Pod Index Label：为 Kubernetes 工作负载编排赋能

## 协同演进：当 Kubernetes 小功能解锁生态系统大创新

在 AI 基础设施领域，我们经常关注最新的 GPU、最快的推理引擎或最复杂的训练框架。但有时，
最具影响力的改进来自于小型基础功能，这些功能使整个生态系统得以演进。这就是**协同演进
（Co-Evolving）**的本质 — 当 Kubernetes 核心能力使下游项目能够以之前不可能或不切实际的方式
进行创新。

今天，我们探讨 [KEP-4017: Pod Index
Label](https://github.com/kubernetes/enhancements/tree/master/keps/sig-apps/4017-pod-index-label)，
这是一个看似简单的功能，已在 Kubernetes 1.32（2024 年 12 月）中达到 GA（正式发布），
并且已经在改变 AI 工作负载的编排、监控和扩展方式。

## 问题：Pod Index 被隐藏了

在 KEP-4017 之前，使用索引化 Pod 的 Kubernetes 工作负载面临一个令人惊讶的限制：

### StatefulSet

StatefulSet 的 Pod 一直都有序数索引（0、1、2...）作为 Pod 名称的一部分（例如 `web-0`、
`web-1`、`web-2`）。然而，这个索引只能通过**解析 Pod 名称**来获取 — 这是一个不优雅的解决
方案，导致以下困难：

- 无法通过 Downward API 在环境变量中使用 Pod 索引
- 无法按 Pod 索引过滤指标和日志
- 无法将流量路由到特定 Pod（例如，始终将请求发送到 `web-0`）
- 无法使用标签选择器按索引选择 Pod

### Indexed Job

Indexed Job（在 Kubernetes 1.24 中引入）为每个 Pod 分配一个完成索引，但此索引仅设置为
**注解**（`batch.kubernetes.io/job-completion-index`），而不是标签。这意味着：

- 无法使用 `kubectl` 或 API 查询按索引选择 Pod
- Service 选择器无法定位特定的 Pod 索引
- 可观测性工具无法轻松按 Pod 索引过滤

## 解决方案：Pod Index 作为标签

KEP-4017 引入了一个简单但强大的变化：**Pod 索引现在作为标签**设置在 StatefulSet 和
Indexed Job 的 Pod 上。

### 实现细节

| 工作负载类型 | 标签键 | 标签值 | 示例 |
| --- | --- | --- | --- |
| **StatefulSet** | `apps.kubernetes.io/pod-index` | Pod 序数（0、1、2...） | `apps.kubernetes.io/pod-index: "0"` |
| **Indexed Job** | `batch.kubernetes.io/job-completion-index` | 完成索引 | `batch.kubernetes.io/job-completion-index: "5"` |

标签在 **Pod 创建时**由相应的控制器设置：

- StatefulSet 控制器在 Pod 创建期间添加 `apps.kubernetes.io/pod-index`
- Job 控制器为 Indexed Job 添加 `batch.kubernetes.io/job-completion-index`（除了现有的注解）

### 推出策略

为避免破坏现有工作负载，KEP-4017 遵循**非破坏性推出策略**：

- **新创建的 Pod** 自动获得标签
- **现有 Pod** 不会被修改（不追溯标记）
- 这意味着现有的 StatefulSet 或 Indexed Job 可能在 Pod 重新创建之前，部分 Pod 有标签，
  部分 Pod 没有标签

这种设计优先考虑稳定性而不是即时一致性，这对生产 Kubernetes 集群来说是正确的权衡。

### 时间线

- **2023-05-17**：KEP 发布
- **Kubernetes 1.28**（2023 年 8 月）：功能进入 **Beta** 阶段，功能门控 `PodIndexLabel`
  默认启用
- **Kubernetes 1.32**（2024 年 12 月）：功能升级为 **GA**（正式发布）

## 用例：LeaderWorkerSet (LWS) 中 Leader 为 Pod-0

Pod 索引标签最引人注目的用例之一是在 **Leader-Worker 架构**中，例如
[LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws) 项目。

### 什么是 LeaderWorkerSet？

LeaderWorkerSet 是一个 Kubernetes 工作负载 API（目前在 SIG Apps 中），专为需要
Leader-Follower 模式的分布式应用程序设计：

- 一个 **Leader Pod** 协调工作负载
- 多个 **Worker Pod** 在 Leader 的协调下执行任务
- 所有 Pod 需要一起启动（Gang Scheduling）
- Leader 需要稳定的身份和可发现的地址

### 挑战：定义 Leader 与 Worker

在传统设置中，Leader 和 Worker Pod 通常在单独的资源中管理：

- **选项 1**：单独的 Deployment — 但这使得 Gang Scheduling 和协调变得困难
- **选项 2**：单独的 StatefulSet — 但这增加了运维复杂性
- **选项 3**：单个 StatefulSet 加上条件逻辑 — 但每个 Pod 如何知道自己是 Leader 还是
  Worker？

### 解决方案：Leader 为 Pod-0

有了 Pod 索引标签，LWS 可以定义一个 StatefulSet，其中：

- **索引为 0 的 Pod**（`apps.kubernetes.io/pod-index: "0"`）是 **Leader**
- **索引 ≥ 1 的 Pod**（`apps.kubernetes.io/pod-index: "1"`、`"2"`...）是 **Worker**

这现在可以轻松实现：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ml-training-leader
spec:
  selector:
    app: ml-training
    apps.kubernetes.io/pod-index: "0"  # 仅选择 Leader Pod
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: ml-training
spec:
  serviceName: "ml-training"
  replicas: 10  # 1 个 Leader + 9 个 Worker
  selector:
    matchLabels:
      app: ml-training
  template:
    metadata:
      labels:
        app: ml-training
    spec:
      containers:
      - name: trainer
        image: ml-training:latest
        env:
        - name: POD_INDEX
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['apps.kubernetes.io/pod-index']
        - name: ROLE
          value: "$([ \"$POD_INDEX\" -eq 0 ] && echo leader || echo worker)"
        - name: LEADER_ADDRESS
          value: "ml-training-leader:8080"
```

### 为什么这对 AI 工作负载很重要

#### 1. 使用参数服务器的分布式训练

在 TensorFlow Parameter Server 或 PyTorch Elastic 等分布式训练架构中：

- **Pod-0** 作为参数服务器或主协调器
- **Pod 1-N** 是训练 Worker
- 参数服务器需要一个稳定的、可发现的地址
- Worker 需要知道它们的 rank/index 以进行梯度聚合

有了 Pod 索引标签：

- 创建一个仅选择 `apps.kubernetes.io/pod-index: "0"` 的 Service
- Worker 通过 DNS 发现参数服务器（`ml-training-leader.default.svc.cluster.local`）
- 每个 Worker 从 Downward API 读取自己的索引以确定其 rank

#### 2. Prefill-Decode 分离的推理

在现代 LLM 推理架构中（参见 [P/D 分离](../../inference/pd-disaggregation.md)），
工作负载被分为：

- **Prefill Worker**：从提示生成初始 KV 缓存
- **Decode Worker**：自回归地生成 Token

LWS 启发的架构（如 [llm-d](https://github.com/llm-d/llm-d) 中使用的架构）利用
Pod 索引标签来：

- 将请求路由到 Pod-0（协调器）
- 根据 Pod 索引动态调度 Prefill 与 Decode 工作
- 按 Pod 索引监控和收集指标以进行性能调优

#### 3. 多副本模型服务

在多模型服务场景中：

- **Pod-0**：服务主要生产模型
- **Pod 1-N**：服务 A/B 测试变体或影子模型

有了 Pod 索引标签，流量路由变得简单：

```yaml
# 生产流量发送到 Pod-0
apiVersion: v1
kind: Service
metadata:
  name: model-production
spec:
  selector:
    app: model-server
    apps.kubernetes.io/pod-index: "0"
---
# 实验流量发送到 Pod-1
apiVersion: v1
kind: Service
metadata:
  name: model-experiment
spec:
  selector:
    app: model-server
    apps.kubernetes.io/pod-index: "1"
```

## 超越 LWS：其他用例

### 1. Ray 集群

[Ray](https://github.com/ray-project/ray) 是用于 AI/ML 工作负载的分布式计算框架。
Ray 集群具有：

- **Head 节点**（Pod-0）：管理集群，调度任务
- **Worker 节点**（Pod 1-N）：执行分布式计算

有了 Pod 索引标签，Ray Operator 可以：

- 创建一个仅定位 Head 节点的 Headless Service
- 配置 Worker 通过 DNS 发现 Head 节点
- 单独监控 Head 节点指标与 Worker 指标

### 2. 可观测性：过滤日志和指标

场景：一个包含 1000 个 Worker 的分布式训练任务失败了。您想检查故障是否源自特定的 Pod
索引。

**KEP-4017 之前**：

```bash
# 痛苦：从所有 Pod 获取日志，grep Pod 名称
kubectl logs -l app=training --prefix | grep "training-42"
```

**KEP-4017 之后**：

```bash
# 优雅：按 Pod 索引标签过滤
kubectl logs -l app=training,apps.kubernetes.io/pod-index=42
```

这也适用于 Prometheus 指标：

```promql
# 仅查询来自 Leader Pod 的指标
sum(gpu_utilization{pod_index="0"})

# 比较不同 Worker 索引的指标
sum by (pod_index) (training_loss{pod_index=~"[1-9].*"})
```

### 3. 混沌工程和测试

有了 Pod 索引标签，混沌工程工具如 [Chaos Mesh](https://chaos-mesh.org/) 可以定位
特定的 Pod 索引：

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: test-leader-failure
spec:
  selector:
    labelSelectors:
      "apps.kubernetes.io/pod-index": "0"  # 杀死 Leader Pod
  mode: one
  action: pod-kill
```

这使得故障场景的可重现测试成为可能：

- 如果 Leader Pod 死亡会发生什么？
- 如果 Worker-5 遇到网络延迟，系统如何表现？

### 4. 滚动部署和蓝绿测试

对于需要手动验证的 StatefulSet 滚动更新：

- 首先更新 Pod-0，验证指标
- 如果成功，推出到 Pod 1-N
- 如果失败，仅回滚 Pod-0

这现在可以轻松脚本化：

```bash
# 仅更新 Pod-0 进行金丝雀测试
kubectl patch statefulset web --type='json' -p='[{"op": "replace", "path":
"/spec/template/spec/containers/0/image", "value":"new-image:v2"}]'
kubectl delete pod web-0  # 仅重启 Pod-0

# 监控 Pod-0 指标
kubectl top pod -l apps.kubernetes.io/pod-index=0

# 如果成功，更新其余部分
kubectl rollout restart statefulset web
```

## 技术影响：最小变化，最大价值

KEP-4017 的美妙之处之一是其**实现复杂性最小**：

### StatefulSet 控制器变更

StatefulSet 控制器中的修复是[添加一个标签的简单操作](https://github.com/kubernetes/kubernetes/pull/119232)：

```go
// 在 newStatefulSetPod() 函数中
pod.Labels[apps.StatefulSetPodIndexLabel] = strconv.Itoa(index)
```

### Job 控制器变更

类似地，Job 控制器[添加了一行](https://github.com/kubernetes/kubernetes/pull/119232)来设置
标签以及现有的注解。

### 大小影响

标签为每个 Pod 增加**约 40 字节**：

- 标签键：`apps.kubernetes.io/pod-index`（29 字节）
- 标签值：`"<index>"`（索引 0-999999 为 1-6 字节）
- 总计：每个 Pod 约 30-35 字节

对于拥有 150,000 个 Pod 的集群（Kubernetes 可扩展性限制），这会增加：

- **约 6 MB** 的额外 etcd 存储
- 对 API Server 内存的影响可忽略不计

这是一个很好的例子，说明**设计良好的小功能如何为生态系统解锁不成比例的价值**。

## 协同演进的故事

KEP-4017 体现了**协同演进**的理念：

1. **Kubernetes 核心**识别基础能力中的差距
2. **社区**在各个 SIG（Apps、Batch、Node）之间讨论用例
3. 提出**简单的增强**，破坏性最小
4. **下游项目**（LWS、Ray、推理平台）采用该功能
5. **整个生态系统**受益于改进的编排、可观测性和效率

这不是一个引起头条关注的华而不实的功能，但它是那种**深思熟虑的渐进式改进**，使
Kubernetes 成为 AI 工作负载的事实标准平台。

## 展望未来：未来的可能性

随着 Pod 索引标签在 Kubernetes 1.32 中稳定，我们可以期待：

### 1. 增强的工作负载 API

- **JobSet**：可以利用 Pod 索引标签进行子作业协调
- **LWS**：已经在整合 Pod 索引标签用于 Leader 选举和服务发现
- **新 CRD**：未来的工作负载控制器可以在此基础上构建

### 2. 更智能的调度

- **拓扑感知调度**：将 Pod-0 放置在高带宽节点上
- **异构资源**：为 Pod-0（参数服务器）分配更多 GPU 内存
- **抢占策略**：在低优先级作业中保护 Pod-0 免受抢占

### 3. AI Gateway 集成

AI Gateway 如 [Envoy AI Gateway](https://github.com/envoyproxy/ai-gateway) 和
[Gateway API Inference Extension](https://github.com/kubernetes-sigs/gateway-api-inference-extension)
可以：

- 将请求路由到特定 Pod 索引以进行 A/B 测试
- 基于 Pod 索引实现粘性会话
- 在 Worker 索引之间进行负载均衡，同时排除 Leader

### 4. 改进的可观测性

可观测性平台（Prometheus、Grafana、OpenTelemetry）可以：

- 在仪表板中提供 Pod 索引作为第一类维度
- 检测特定 Pod 索引中的异常
- 将 Pod 索引与硬件拓扑（NUMA、GPU 亲和性）关联

## 如何今天就使用它

### 检查您的 Kubernetes 版本

Pod 索引标签可在以下版本中使用：

- **Kubernetes 1.28+**（Beta，功能门控默认启用）
- **Kubernetes 1.32+**（GA，始终启用）

```bash
kubectl version --short
```

### 验证现有工作负载上的标签

```bash
# 对于 StatefulSet
kubectl get pods -l app=your-statefulset -o yaml | grep pod-index

# 对于 Indexed Job
kubectl get pods -l job-name=your-job -o yaml | grep job-completion-index
```

### 创建具有 Pod Index 意识的新 StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: distributed-training
spec:
  serviceName: "training"
  replicas: 4
  selector:
    matchLabels:
      app: training
  template:
    metadata:
      labels:
        app: training
    spec:
      containers:
      - name: trainer
        image: pytorch/pytorch:latest
        env:
        - name: POD_INDEX
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['apps.kubernetes.io/pod-index']
        - name: WORLD_SIZE
          value: "4"
        - name: IS_MASTER
          value: "$([ \"$POD_INDEX\" -eq 0 ] && echo true || echo false)"
```

### 创建定位特定索引的 Service

```yaml
# Master 节点（Pod-0）的 Service
apiVersion: v1
kind: Service
metadata:
  name: training-master
spec:
  selector:
    app: training
    apps.kubernetes.io/pod-index: "0"
  ports:
  - port: 29500
    name: master-port
---
# 所有 Worker（Pod-1、Pod-2、Pod-3）的 Service
apiVersion: v1
kind: Service
metadata:
  name: training-workers
spec:
  selector:
    app: training
  ports:
  - port: 29500
    name: worker-port
```

## 结论：小功能，大影响

KEP-4017 是**基础 Kubernetes 增强如何促进生态系统创新**的完美例子。通过将 Pod 索引作为
标签公开，Kubernetes 已经：

- **简化了 Leader-Worker 架构**，如 LeaderWorkerSet
- **改进了分布式 AI 工作负载的可观测性**
- **为模型服务启用了更智能的流量路由**
- **简化了测试和混沌工程**

这就是**协同演进**的本质：Kubernetes 不需要直接解决每个 AI 基础设施挑战。相反，它提供
正确的原语 — 而生态系统构建解决方案。

当您设计下一个 AI 基础设施平台时，请考虑：

- 如何利用 Pod 索引标签进行 Leader 选举？
- 是否可以通过使用 Pod-0 作为协调器来简化编排逻辑？
- 您的指标和日志是否可按 Pod 索引过滤？

该功能已经到来，它已经稳定，并且已经准备好解锁您的下一个创新。

## 参考资料

- [KEP-4017: Pod Index
  Label](https://github.com/kubernetes/enhancements/tree/master/keps/sig-apps/4017-pod-index-label)
- [LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws)
- [Kubernetes StatefulSet
  文档](https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/statefulset/)
- [Kubernetes Indexed
  Job](https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/job/)
- [Pod Index Label GA
  公告](https://kubernetes.io/blog/2024/12/17/statefulset-podindexlabel-ga/)
- [Prefill-Decode 分离指南](../../inference/pd-disaggregation.md)
- [LWS Gang Scheduling
  KEP](https://github.com/kubernetes-sigs/lws/blob/main/keps/407-gang-scheduling/README.md)

---

*本博客文章是 AI-Infra 学习系列的一部分，专注于 Kubernetes 和云原生技术如何演进以支持现代
AI 工作负载。*
