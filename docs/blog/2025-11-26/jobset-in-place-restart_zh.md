---
status: Active
maintainer: pacoxu
date: 2025-11-26
tags: kubernetes, jobset, in-place-restart, co-evolving, batch-processing
canonical_path: docs/blog/2025-11-26/jobset-in-place-restart_zh.md
---

# JobSet 原地重启：从 2 分 10 秒到 10 秒 — 速度提升 92%

## 协同演进：当 Kubernetes 能力赋能整个生态

在快速发展的 AI 基础设施领域，一种美妙的协同效应正在涌现：Kubernetes 社区开发基础能力，而下游
项目如 [JobSet](https://github.com/kubernetes-sigs/jobset)、
[Ray](https://github.com/ray-project/ray) 和
[LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws) 采用这些特性来显著提升
效率。我们称之为**协同演进（Co-Evolving）**— 整个生态系统共同向前演进。

Kubernetes 最近引入了越来越多与 AI 相关的能力，但要在 AI 工作负载中充分发挥这些能力的潜力，
需要其他项目的适配。今天，我们将探讨一个典型案例：**JobSet 利用 Kubernetes 原地容器重启实现
92% 的重启速度提升**。

## 问题：JobSet 重启速度慢

当运行在 [JobSet](https://github.com/kubernetes-sigs/jobset) 上的分布式训练任务需要重启
（由于临时故障、配置更新或检查点恢复）时，传统方法涉及：

1. **删除 JobSet 中的所有 Pod**
2. **等待 Pod 终止**完成
3. 通过 Kubernetes 调度器**重新调度所有 Pod**
4. **等待 Pod 启动**（包括镜像拉取、init 容器等）

在拥有 5000 节点的大规模集群中，这个过程大约需要 **2 分 10 秒**。对于快速恢复至关重要的
AI/ML 工作负载来说，这个开销是巨大的。

## 解决方案：原地容器重启

Kubernetes 引入了允许容器在不重建 Pod 的情况下重启的能力：

### KEP-5307：容器重启策略（Kubernetes 1.34）

[KEP-5307](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5307-container-restart-policy/README.md)
引入了对 Pod 内单个容器重启行为的细粒度控制。这允许：

- 为每个容器指定重启策略（而不仅仅是每个 Pod）
- 在不影响整个 Pod 的情况下触发容器重启
- 在容器重启期间保持 Pod 身份、IP 和卷

### KEP-5532：容器退出时重启所有容器（Kubernetes 1.35）

[KEP-5532](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5532-restart-all-containers-on-container-exits/README.md)
扩展了这一能力以支持协调重启：

- 当特定容器退出时重启 Pod 中的所有容器
- 作为 Pod 生命周期的一部分重启 init 容器和 sidecar
- 在不重建 Pod 的情况下实现 Pod 级别的重启协调

## 真实成果：JobSet 原地重启

JobSet 团队开发了一个
[原地重启原型](https://github.com/kubernetes-sigs/jobset/compare/main...GiuseppeTT:jobset:in-place-restart-prototype)，
展示了显著的性能提升：

| 指标 | 传统重启 | 原地重启 | 改进 |
| --- | --- | --- | --- |
| 重启时间 | 2 分 10 秒 | 10 秒 | **快 92%** |
| 测试规模 | 5000 节点 | 5000 节点 | - |
| 调度开销 | 高 | 无 | 已消除 |
| Pod 重建 | 需要 | 不需要 | 已避免 |

详细设计信息请参阅
[JobSet 原地重启设计文档](https://docs.google.com/document/d/16zexVooHKPc80F4dVtUjDYK9DOpkVPRNfSv0zRtfFpk/edit?tab=t.0#heading=h.y6xl7juq7465)。

## 为什么这对 AI 工作负载很重要

### 1. 分布式训练恢复

大规模分布式训练任务（PyTorch DDP、TensorFlow MultiWorkerMirroredStrategy）对重启延迟
特别敏感：

- **检查点恢复**：故障后，所有 worker 需要从最新检查点重启。原地重启使 worker 恢复速度
  快 12 倍。
- **梯度同步**：所有 worker 必须运行才能继续训练。更快的重启意味着更少的 GPU 时间浪费。
- **成本节省**：在昂贵的 GPU 集群上（每 GPU 小时 $2-10），每次重启节省 2 分钟会累积成
  可观的金额。

### 2. 作业依赖

许多 AI 流水线有复杂的作业依赖。当作业重启时：

- **下游作业**等待上游完成
- **Gang 调度约束**要求所有 worker 都存在
- **网络连接**必须为集合操作保持

原地重启保留了 Pod 身份和网络连接，最大限度地减少对整体流水线的干扰。

### 3. 资源效率

传统重启涉及：

- **调度器负载**：为可能数千个 Pod 找到节点
- **API 服务器负载**：创建/删除 Pod 对象
- **节点准备**：镜像拉取、卷挂载、init 容器

原地重启消除了所有这些开销，将资源保留给实际工作负载。

## 工作原理

### 之前：传统重启流程

```text
触发作业重启
    ↓
删除所有 Pod → 等待终止 (30秒+)
    ↓
创建新 Pod → 等待调度 (30秒+)
    ↓
拉取镜像（如需要）→ 启动容器 (60秒+)
    ↓
总计：约 2 分 10 秒
```

### 之后：原地重启流程

```text
触发作业重启
    ↓
发送容器退出信号 → 容器原地重启 (10秒)
    ↓
总计：约 10 秒
```

关键区别：

1. **不删除 Pod**：Pod 对象保留，保持身份
2. **不重新调度**：Pod 保持在当前节点
3. **不拉取镜像**：镜像已在节点上缓存
4. **立即重启**：容器进程直接重启

## 实现考虑因素

### 何时使用原地重启

- **临时故障**：容器崩溃、OOM kill、网络超时
- **配置更新**：重启以获取新的环境变量
- **检查点恢复**：从保存的状态恢复训练
- **滚动更新**：按顺序优雅地重启 worker

### 何时需要传统重启

- **节点故障**：Pod 必须移动到健康节点
- **资源变更**：Pod 需要更多/更少资源（考虑 VPA）
- **镜像更新**：需要新的容器镜像
- **拓扑变更**：Pod 需要不同的放置

### 与 JobSet 集成

JobSet 可以通过以下方式利用原地重启：

```yaml
apiVersion: jobset.x-k8s.io/v1alpha2
kind: JobSet
metadata:
  name: distributed-training
spec:
  replicatedJobs:
  - name: workers
    replicas: 8
    template:
      spec:
        template:
          spec:
            restartPolicy: Always  # 启用原地重启
            containers:
            - name: trainer
              image: pytorch/pytorch:latest
```

## 更广泛的协同演进模式

这个 JobSet 改进是云原生 AI 中协同演进模式的典型案例：

| Kubernetes 能力 | 项目采用 | 收益 |
| --- | --- | --- |
| 原地重启 | JobSet | 恢复速度快 92% |
| Gang 调度 (1.35) | Kueue, LWS | 全有或全无放置 |
| DRA (1.34 GA) | NVIDIA GPU Operator | 灵活的设备分配 |
| Workload API (1.35) | Volcano, YuniKorn | 原生工作负载支持 |

随着 Kubernetes 继续添加对 AI 友好的特性，我们期待更多项目采用它们，创造一个良性的改进循环。

## 入门指南

### 前提条件

- Kubernetes 1.34+（对于 KEP-5307）
- Kubernetes 1.35+（对于 KEP-5532 Pod 级别重启）
- 支持原地重启的 JobSet（请查看最新版本）

### 启用功能门控

```bash
# 在 kube-apiserver 和 kubelet 上
--feature-gates=InPlacePodVerticalScaling=true

# 对于 1.35+ Pod 级别重启功能
--feature-gates=SidecarContainers=true
```

### 测试原地重启

1. 部署一个带有 `restartPolicy: Always` 的 JobSet
2. 触发容器重启（例如，`kubectl exec ... -- kill -TERM 1`）
3. 观察与 Pod 重建相比的重启时间

## 未来路线图

原地重启能力持续演进：

- **KEP-5307 升级**：向 Beta/GA 迈进
- **KEP-5532 升级**：增强的 Pod 级别重启控制
- **JobSet 集成**：对原地重启策略的原生支持
- **监控**：更好的重启事件可观测性
- **Kueue 集成**：工作负载感知的重启处理

## 结论

JobSet 原地重启优化展示了 Kubernetes 生态系统中协同演进的力量。通过采用上游 Kubernetes 能力，
项目可以实现显著的性能改进：

- **重启速度快 92%**（2 分 10 秒 → 10 秒）
- **无调度开销**
- **保留 Pod 身份和网络**
- **减少 API 服务器负载**

这只是 Kubernetes 社区和下游项目如何共同努力提高 AI 工作负载效率的一个例子。随着更多与 AI
相关的特性在 Kubernetes 中落地，我们可以期待 JobSet、Ray、LWS 等项目带来更多优化。

AI 基础设施的未来是协同演进的 — 而这正在发生。

---

## 参考资料

### KEP 和文档

- [KEP-5307：容器重启策略](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5307-container-restart-policy/README.md)
- [KEP-5532：容器退出时重启所有容器](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5532-restart-all-containers-on-container-exits/README.md)
- [KEP-1287：Pod 原地垂直扩展](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/1287-in-place-update-pod-resources/README.md)
- [JobSet 原地重启设计文档](https://docs.google.com/document/d/16zexVooHKPc80F4dVtUjDYK9DOpkVPRNfSv0zRtfFpk/edit?tab=t.0#heading=h.y6xl7juq7465)
- [JobSet 原地重启原型](https://github.com/kubernetes-sigs/jobset/compare/main...GiuseppeTT:jobset:in-place-restart-prototype)

### 相关项目

- [JobSet](https://github.com/kubernetes-sigs/jobset) - Kubernetes SIG Apps
- [LeaderWorkerSet](https://github.com/kubernetes-sigs/lws) - Kubernetes SIG Apps
- [Kueue](https://github.com/kubernetes-sigs/kueue) - Kubernetes SIG Scheduling
- [Volcano](https://github.com/volcano-sh/volcano) - CNCF 孵化中

### 相关博客文章

- [Kubernetes 中的 Gang 调度](./gang-scheduling_zh.md)
- [调度优化](../../kubernetes/scheduling-optimization.md)

---

**作者**：AI 基础设施学习路径  
**日期**：2025 年 11 月 26 日  
**标签**：#kubernetes #jobset #原地重启 #协同演进 #ai基础设施
