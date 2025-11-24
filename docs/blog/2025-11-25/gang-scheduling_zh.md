---
status: Active
maintainer: pacoxu
date: 2025-11-24
tags: kubernetes, scheduling, gang-scheduling, workload-api, batch-processing
canonical_path: docs/blog/2025-11-25/gang-scheduling_zh.md
---

# Gang Scheduling 来到 Kubernetes：AI/ML 工作负载的游戏规则改变者

## 引言

在 Kubernetes 中调度大型工作负载一直是一个挑战。当你需要运行分布式训练任务、批处理作业或其他多
Pod 应用时，传统的逐个 Pod 调度方法可能导致资源浪费、死锁和低效。今天，我们很高兴分享关于
**工作负载感知调度（Workload Aware Scheduling）**计划的见解，它正在改变 Kubernetes 处理多
Pod 工作负载的方式。

## 传统 Pod 调度的问题

在传统的 Kubernetes 调度中，每个 Pod 都是独立调度的。对于分布式工作负载，例如：

- **分布式机器学习训练**（如 PyTorch、TensorFlow 多 worker 任务）
- **批处理**（如 Apache Spark、Ray 集群）
- **高性能计算**（如 MPI 应用）

这种独立调度会产生几个问题：

1. **部分调度死锁**：一些 Pod 被调度，而其他 Pod 无限期等待资源
2. **资源浪费**：已调度的 Pod 占用资源但无法启动工作，直到所有对等 Pod 就绪
3. **集群利用率低**：资源被不完整的工作负载占用
4. **不可预测的作业完成时间**：作业可能在部分调度状态下等待数小时甚至数天

## Kubernetes v1.35：工作负载感知调度

Kubernetes 社区在 v1.35 中引入了**工作负载感知调度**，包含三个主要组件：

### 1. Workload API（Alpha）

`scheduling.k8s.io/v1alpha1` 中新的 `Workload` API 资源提供了一种结构化的方式来定义多
Pod 应用的调度需求。

```yaml
apiVersion: scheduling.k8s.io/v1alpha1
kind: Workload
metadata:
  name: training-job-workload
  namespace: ml-workloads
spec:
  podGroups:
  - name: workers
    policy:
      gang:
        # 全有或全无：仅当 4 个 Pod 可以一起运行时才调度
        minCount: 4
```

将你的 Pod 链接到工作负载：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: worker-0
  namespace: ml-workloads
spec:
  workloadRef:
    name: training-job-workload
    podGroup: workers
  containers:
  - name: trainer
    image: my-ml-framework:latest
    resources:
      requests:
        nvidia.com/gpu: 1
```

### 2. Gang Scheduling（Alpha）

Gang Scheduling 实现了**全有或全无**的放置策略：

**工作原理：**

1. **等待阶段**：当 Pod 到达时，调度器会阻止它们，直到有 `minCount` 个 Pod 处于待处理状态
2. **评估阶段**：调度器尝试为 gang 中的所有 Pod 找到合适的节点
3. **决策阶段**：
   - ✅ **成功**：如果所有 Pod 都可以放置，它们将一起绑定到节点
   - ❌ **失败**：如果任何 Pod 在超时时间（5 分钟）内无法放置，所有 Pod 都将被拒绝并重新排队

这防止了资源浪费，并确保你的分布式工作负载要么完全运行，要么等待足够的资源。

**主要优势：**

- 消除部分调度死锁
- 通过为可运行的工作负载释放资源来提高集群利用率
- 为分布式应用提供可预测的行为
- 与 Pod 抢占和自动扩展无缝协作

### 3. Opportunistic Batching（Beta）

Opportunistic Batching（机会批处理）是一种性能优化，可以加速相同 Pod 的调度，无需任何配置更改。

**工作原理：**

当调度器处理具有相同调度需求（相同资源、镜像、亲和性等）的 Pod 时，它可以为队列中的后续 Pod 重
用可行性计算和评分结果。

**性能影响：**

- 大幅减少大型同构工作负载的调度延迟
- 可以将批处理工作负载的调度吞吐量提高 5-10 倍
- 透明工作 - 无需用户配置
- 在 Kubernetes v1.35 中默认启用（Beta）

**当前限制：**

- 对使用拓扑分布约束的 Pod 禁用
- 对使用动态资源分配（DRA）的 Pod 禁用
- 所有与调度相关的 Pod 字段必须相同

## 实际使用场景

### 分布式机器学习训练

```yaml
apiVersion: scheduling.k8s.io/v1alpha1
kind: Workload
metadata:
  name: pytorch-training
spec:
  podGroups:
  - name: workers
    policy:
      gang:
        minCount: 8  # 分布式训练需要 8 个 GPU
```

你的 PyTorch 分布式训练作业只有在所有 8 个 worker 都可以调度时才会启动，防止 GPU 资源浪费。

### Kubernetes 上的 Apache Spark

```yaml
apiVersion: scheduling.k8s.io/v1alpha1
kind: Workload
metadata:
  name: spark-job
spec:
  podGroups:
  - name: executors
    policy:
      gang:
        minCount: 10  # 最少 1 个 driver + 9 个 executor
```

使用 gang scheduling 的 Spark 作业避免了 driver 启动但 executor 无法调度的常见问题。

### Ray 集群

Ray 应用程序通过 gang scheduling 受益，确保头节点和工作节点一起启动，实现即时分布式计算。

## 路线图：1.36 及以后的计划

工作负载感知调度工作对 Kubernetes 1.36 有着雄心勃勃的路线图：

### v1.36 计划

- **扩展 Workload API**：基于 alpha 反馈增强功能和改进
- **Job、StatefulSet、JobSet 的自动工作负载**：为常见 Kubernetes 资源自动创建工作负载
- **拓扑感知调度**：在放置 gang 成员时考虑网络和硬件拓扑
- **单周期工作负载调度**：在单个调度周期内调度整个 gang 以获得更好的性能
- **基于树的工作负载调度算法**：更高效的 gang 放置决策
- **改进的绑定过程**：使用提名更好地处理 kubelet 竞争
- **延迟抢占**：在实际驱逐之前引入提名受害者的概念
- **工作负载级别的抢占**：抢占整个 gang 而不是单个 Pod

### 长期愿景

最终目标是使 Kubernetes 原生理解和优化工作负载级别的操作，包括：

- 与集群自动扩展深度集成
- 工作负载感知的资源配额和限制
- 更好地支持混合工作负载类型（批处理 + 服务）
- 增强多 Pod 应用的可观测性

## 即将发布的官方博客文章

Kubernetes 社区正在准备关于工作负载感知调度的官方博客文章，将很快在
Kubernetes 博客上发布。请关注
[kubernetes/website#53012](https://github.com/kubernetes/website/pull/53012)
的合并以获取官方公告。

## 入门指南

### 前提条件

- Kubernetes v1.35 或更高版本
- 在 kube-apiserver 和 kube-scheduler 上配置功能门控

### 启用 Workload API 和 Gang Scheduling

```bash
# 在 kube-apiserver 上
--feature-gates=GenericWorkload=true
--runtime-config=scheduling.k8s.io/v1alpha1=true

# 在 kube-scheduler 上
--feature-gates=GenericWorkload=true,GangScheduling=true
```

### 启用 Opportunistic Batching

Opportunistic Batching 在 v1.35 中作为 Beta 功能**默认启用**。要禁用它：

```bash
# 在 kube-scheduler 上
--feature-gates=OpportunisticBatching=false
```

### 测试 Gang Scheduling

1. 创建 Workload 资源
2. 创建带有指向 Workload 的 `workloadRef` 的 Pod
3. 观察 kube-scheduler 日志中的调度行为
4. 监控 gang scheduling 成功/失败率的指标

## 最佳实践

1. **设置适当的 minCount**：考虑你的应用的最小可行大小
2. **准确使用资源请求**：Gang scheduling 依赖于准确的资源需求
3. **监控调度指标**：跟踪 gang scheduling 成功率和超时事件
4. **与集群自动扩展一起测试**：确保你的自动扩展器可以为 gang 配置节点
5. **规划失败场景**：了解超时行为和重试逻辑

## 与现有解决方案的比较

在原生 gang scheduling 之前，用户依赖于：

- **Volcano**：CNCF 孵化项目，具有 gang scheduling
- **Kueue**：Kubernetes SIG 项目，用于队列和配额管理
- **YuniKorn**：Apache 项目，支持 gang scheduling
- **自定义调度器**：针对特定用例的内部解决方案

**为什么使用原生 gang scheduling？**

- 由 Kubernetes SIG Scheduling 维护
- 与核心调度器功能集成（抢占、自动扩展）
- 无需部署和维护额外组件
- 最终成为 Kubernetes 一致性套件的一部分

**何时使用外部调度器？**

- 今天就需要生产就绪的 gang scheduling（使用 Volcano 或 Kueue）
- 需要超出当前 Kubernetes 路线图的功能
- 在特定调度器上有现有投资

## 资源和参考

### KEP 和文档

- [KEP-4671: Gang Scheduling](https://github.com/kubernetes/enhancements/issues/4671)
- [KEP-5598: Opportunistic Batching](https://github.com/kubernetes/enhancements/blob/master/keps/sig-scheduling/5598-opportunistic-batching/README.md)
- [工作负载感知调度跟踪问题](https://github.com/kubernetes/kubernetes/issues/132192)
- [Kubernetes Website PR #53012](https://github.com/kubernetes/website/pull/53012)

### 相关项目

- [Volcano Scheduler](https://github.com/volcano-sh/volcano) - CNCF 孵化中
- [Kueue](https://github.com/kubernetes-sigs/kueue) - Kubernetes SIG 项目
- [YuniKorn](https://yunikorn.apache.org/) - Apache 项目

### 社区

- SIG Scheduling: <https://github.com/kubernetes/community/tree/master/sig-scheduling>
- Slack: Kubernetes Slack 上的 #sig-scheduling

## 结论

Gang Scheduling 和工作负载感知调度代表了 Kubernetes 在支持 AI/ML、HPC 和批处理工作负载方面的
重大进步。v1.35 alpha 版本为原生多 Pod 调度提供了基础，并为 v1.36 及以后提供了令人兴奋的路线图。

我们鼓励社区：

- 在开发环境中测试这些功能
- 通过 GitHub 问题提供反馈
- 分享用例和需求
- 为持续开发做出贡献

Kubernetes 调度的未来是工作负载感知的，这段旅程才刚刚开始！

---

**作者**：AI 基础设施学习路径  
**日期**：2025 年 11 月 24 日  
**标签**：#kubernetes #scheduling #gangscheduling #ai-ml #batch-processing
