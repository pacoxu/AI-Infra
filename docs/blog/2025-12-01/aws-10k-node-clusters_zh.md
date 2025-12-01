---
status: Active
maintainer: pacoxu
date: 2025-12-01
tags: kubernetes, large-scale, aws, eks, scalability, etcd, image-pull
canonical_path: docs/blog/2025-12-01/aws-10k-node-clusters_zh.md
---

# AWS 万节点 EKS 超大规模集群：深度解析

继我们之前对 [Google 13 万节点集群](../../kubernetes/large-scale-clusters.md)的介绍后，
本文探讨 Amazon EKS 如何实现万节点以上的超大规模部署。基于 AWS 博客文章
[Under the Hood: Amazon EKS Ultra Scale Clusters](https://aws.amazon.com/cn/blogs/containers/under-the-hood-amazon-eks-ultra-scale-clusters/)，
我们将分析社区通用优化和 AWS 特有创新。

## 概述

AWS EKS 超大规模集群面向需要海量算力的 AI/ML 工作负载。在这个规模下的主要挑战包括：

- **API Server 压力**：处理数百万请求
- **etcd 性能**：存储后端瓶颈
- **镜像分发**：在数千节点间快速拉取容器镜像
- **调度效率**：大规模 Pod 调度
- **可观测性**：监控和扩展支撑服务

**AWS 规模下的性能 SLO**：

| 操作 | 目标延迟 |
| --- | --- |
| GET/PUT 请求 | < 1 秒 |
| LIST 请求 | < 30 秒 |
| 调度器吞吐量 | 500 pods/秒 |

## 第一部分：社区通用优化

在深入 AWS 特有优化之前，先了解上游 Kubernetes 对所有大规模部署都有益的改进。

### 从缓存一致性读取（Kubernetes v1.33）

**问题**：在大规模下，每个 API Server 读取都命中 etcd 会造成不可承受的负载。

**解决方案**：Kubernetes v1.33 引入了 API Server 缓存层的改进，使更多读取可以直接从
缓存提供，同时保持一致性保证。

**核心特性**：

- 基于 Watch 的缓存与 etcd 保持同步
- 资源版本确保一致性
- 显著降低 etcd 读取负载

**影响**：集群可以处理数百万 API 请求而不会压垮 etcd。实现细节参见
[KEP-2340: Consistent Reads from Cache](https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/2340-Consistent-reads-from-cache)。

### Karpenter：即时节点供给

[Karpenter](https://github.com/kubernetes-sigs/karpenter) 是一个 Kubernetes 节点
供给器，提供：

- **快速扩展**：秒级供给节点，而非分钟级
- **精准选型**：为待调度 Pod 选择最优实例类型
- **成本优化**：自动整合工作负载
- **多架构支持**：无缝处理 ARM 和 x86 实例

**Karpenter 在大规模下的重要性**：

传统 Cluster Autoscaler 需要预定义节点组，响应较慢。Karpenter 直接监听待调度 Pod 并
精确供给合适的实例，显著减少调度时间。

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ai-workloads
spec:
  template:
    spec:
      requirements:
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["p5.48xlarge", "p4d.24xlarge"]
      expireAfter: 720h
```

**社区替代方案**：

- **Cluster Autoscaler**：传统方案，基于节点组工作
- **Koordinator**：支持 QoS 保证的高级调度
- **Volcano**：AI/ML 工作负载的批处理调度

## 第二部分：AWS 特有优化

### etcd 后端：Amazon QLDB Journal

**挑战**：标准 etcd 使用 Raft 共识在超大规模下可能成为瓶颈，尤其是写入密集型工作负载。

**AWS 方案**：用 Amazon QLDB（量子账本数据库）journal 替代 Raft 作为 etcd 后端：

| 组件 | 标准 etcd | AWS EKS 超大规模 |
| --- | --- | --- |
| 共识 | Raft | Amazon QLDB Journal |
| 写入吞吐量 | 受 Raft 限制 | 更高吞吐量 |
| 持久性 | 基于磁盘 | 托管账本 |
| 运维开销 | 自行管理 | AWS 托管 |

**工作原理**：

1. etcd 写入发送到 QLDB journal 而非本地磁盘
2. QLDB 提供仅追加、不可变的存储
3. 通过 QLDB 的事务模型保持一致性

**社区替代方案**：

- **Spanner**（Google）：GKE 13 万+节点使用
- **TiKV** + kubebrain：字节跳动 2 万节点方案
- **Kine**：使用 MySQL/PostgreSQL 的轻量级替代

### etcd BoltDB 使用 tmpfs

**问题**：BoltDB（etcd 的存储引擎）在高 I/O 负载下性能下降。

**解决方案**：将 BoltDB 存储挂载到 tmpfs（基于内存的文件系统）：

- **收益**：消除磁盘 I/O 延迟
- **权衡**：需要足够内存，数据持久性由 QLDB 处理
- **效果**：etcd 操作速度显著提升

这一技术与 QLDB journal 结合时特别有效，因为持久性由 QLDB 保证，而性能来自基于内存
的操作。

### 镜像拉取加速：SOCI Snapshotter

在万节点规模下，容器镜像分发成为关键瓶颈。AWS 使用
[SOCI (Seekable OCI)](https://github.com/awslabs/soci-snapshotter) 实现容器镜像
的懒加载。

**SOCI 工作原理**：

1. **索引生成**：为容器镜像创建可寻址索引
2. **懒加载**：容器立即启动，按需拉取层
3. **后台获取**：容器运行时继续下载剩余层

**性能影响**：

| 镜像大小 | 传统拉取 | SOCI 懒加载 | 提升 |
| --- | --- | --- | --- |
| 1 GB | ~30 秒 | ~2 秒 | 快 93% |
| 5 GB | ~150 秒 | ~3 秒 | 快 98% |
| 10 GB | ~300 秒 | ~5 秒 | 快 98% |

**社区替代方案**：

| 方案 | 方式 | 适用场景 |
| --- | --- | --- |
| **SOCI** | 懒加载 | AWS，大镜像 |
| **Nydus** | 懒加载 | 通用，Dragonfly 集成 |
| **Stargz** | 懒加载 | containerd 原生 |
| **Dragonfly** | P2P 分发 | 大集群，带宽受限 |
| **Spegel** | P2P 分发 | 轻量级，集群本地 |
| **Kraken** | P2P 分发 | Uber，极大规模 |

更多镜像优化内容，参见
[Pod 启动速度](../../kubernetes/pod-startup-speed.md#image-optimization)。

### CoreDNS 自动扩容

**问题**：DNS 查询随集群规模增长。在万节点时，CoreDNS 可能不堪重负。

**解决方案**：基于集群规模的 CoreDNS 比例扩容：

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: coredns
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: coredns
  minReplicas: 2
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

**最佳实践**：

- CoreDNS Pod 数量与节点数成比例扩展
- 使用 NodeLocal DNSCache 减少 CoreDNS 负载
- 将 DNS 延迟作为关键 SLI 监控

### LWS + vLLM 用于 LLM 推理

对于大规模 LLM 推理，AWS 推荐：

**[LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws)**：

- 管理 leader-worker 拓扑结构的 Pod 组
- 支持高效分布式推理
- 提供稳定的网络身份

**[vLLM](https://github.com/vllm-project/vllm)**：

- 高吞吐量 LLM 服务引擎
- PagedAttention 高效内存使用
- 连续批处理提升 GPU 利用率

**示例部署**：

```yaml
apiVersion: leaderworkerset.x-k8s.io/v1
kind: LeaderWorkerSet
metadata:
  name: vllm-inference
spec:
  replicas: 4
  leaderWorkerTemplate:
    size: 8
    leaderTemplate:
      spec:
        containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          resources:
            limits:
              nvidia.com/gpu: 8
```

更多推理优化内容，参见[推理指南](../../inference/README.md)。

## 对比：AWS vs Google vs 社区

| 优化项 | AWS EKS | Google GKE | 社区 |
| --- | --- | --- | --- |
| **存储后端** | QLDB journal | Spanner | TiKV, Kine |
| **读缓存** | API server 缓存 | 一致性读取 | KEP-2340 |
| **镜像加速** | SOCI | gcr.io 优化 | Nydus, Dragonfly |
| **节点供给** | Karpenter | GKE Autopilot | Cluster Autoscaler |
| **DNS 扩展** | CoreDNS 自动扩容 | 自定义 | NodeLocal DNS |
| **目标规模** | 1 万节点 | 13 万节点 | 5 千节点（默认） |

## 实施建议

### 生产部署

1. **从社区优化开始**：
   - 启用缓存一致性读取
   - 使用 Karpenter 或 Cluster Autoscaler
   - 实施镜像懒加载（Nydus/Stargz）

2. **添加平台特定功能**：
   - AWS：SOCI，托管 etcd 后端
   - GKE：Spanner 后端，原生优化
   - 私有化：TiKV，优化的 etcd 集群

3. **监控关键 SLI**：
   - API Server 延迟（GET p99 < 1s）
   - etcd 延迟和磁盘 I/O
   - 调度器吞吐量
   - DNS 查询延迟

### 架构概览

```text
┌─────────────────────────────────────────────────────────┐
│                    控制平面                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │API Server│  │API Server│  │     API Server       │  │
│  │ (缓存)   │  │ (缓存)   │  │      (缓存)          │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│       │             │                    │              │
│       └─────────────┼────────────────────┘              │
│                     │                                    │
│              ┌──────▼──────┐                            │
│              │ etcd 集群   │                            │
│              │ (QLDB/tmpfs)│                            │
│              └──────────────┘                           │
├─────────────────────────────────────────────────────────┤
│                    数据平面                              │
│  ┌────────┐ ┌────────┐ ┌────────┐        ┌────────┐   │
│  │节点 1  │ │节点 2  │ │节点 3  │  ...   │节点 1万│   │
│  │(SOCI)  │ │(SOCI)  │ │(SOCI)  │        │(SOCI)  │   │
│  └────────┘ └────────┘ └────────┘        └────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 总结

AWS EKS 超大规模集群证明，万节点以上的 Kubernetes 部署是可行的，通过以下组合实现：

- **上游改进**：一致性读取，更好的缓存
- **存储优化**：替代后端，基于内存的存储
- **镜像加速**：SOCI 懒加载
- **智能扩展**：Karpenter，CoreDNS 自动扩容
- **工作负载优化**：LWS + vLLM 用于 AI 推理

虽然 AWS 和 Google 采取不同方法（QLDB vs Spanner，SOCI vs 原生优化），但底层原则
相似：减轻 etcd 压力，加速镜像分发，优化调度。

对于构建大规模 Kubernetes 集群的组织，关键是从社区最佳实践开始，根据需要叠加平台
特定优化。

---

## 参考资料

### AWS 资源

- [Under the Hood: Amazon EKS Ultra Scale Clusters](https://aws.amazon.com/cn/blogs/containers/under-the-hood-amazon-eks-ultra-scale-clusters/)
- [SOCI Snapshotter](https://github.com/awslabs/soci-snapshotter)
- [Karpenter](https://github.com/kubernetes-sigs/karpenter)

### 社区资源

- [KEP-2340: Consistent Reads from Cache](https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/2340-Consistent-reads-from-cache)
- [大型集群最佳实践](https://kubernetes.io/zh-cn/docs/setup/best-practices/cluster-large/)
- [SIG Scalability](https://github.com/kubernetes/community/tree/master/sig-scalability)

### 相关文档

- [大规模 Kubernetes 集群](../../kubernetes/large-scale-clusters.md)
- [Pod 启动速度](../../kubernetes/pod-startup-speed.md)
- [推理指南](../../inference/README.md)

---

**作者**：AI 基础设施学习路径
**日期**：2025 年 12 月 1 日
**标签**：#kubernetes #aws #eks #大规模 #etcd #镜像拉取
