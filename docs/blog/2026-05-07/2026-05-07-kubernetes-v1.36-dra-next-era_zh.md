---
status: Active
maintainer: pacoxu
date: 2026-05-07
last_updated: 2026-05-08
tags: kubernetes, dra, scheduling, device-management, ai-infrastructure
canonical_path: docs/blog/2026-05-07/2026-05-07-kubernetes-v1.36-dra-next-era_zh.md
source_urls:
  - https://kubernetes.io/blog/2026/05/07/kubernetes-v1-36-dra-136-updates/
  - https://kubernetes.io/blog/2025/09/01/kubernetes-v1-34-dra-updates/
  - https://kubernetes.io/blog/2025/05/01/kubernetes-v1-33-dra-updates/
  - https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/
  - https://pkg.go.dev/k8s.io/dynamic-resource-allocation/kubeletplugin
---

# Kubernetes v1.36：更多驱动程序、新特性，以及 DRA 的下一个时代

动态资源分配（DRA）从根本上改变了平台管理员在 Kubernetes 中处理硬件加速器和
专用资源的方式。在 `v1.36` 中，DRA 继续走向成熟，带来了一批特性进阶、关键的
可用性改进，以及一些新的能力：将 DRA 的灵活性扩展到内存和 CPU 这类原生资源，
并支持在 `PodGroup` 中使用 `ResourceClaim`。

驱动程序的可用性也在持续扩展。除了专用计算加速器之外，这一生态系统还已经涵盖
对网络和其他硬件类型的支持，这反映出它正迈向一种更稳健、与具体硬件无关的基础
设施形态。

无论你是在管理大规模 GPU 集群，需要更好地处理故障，还是只是希望找到更好的方式
来定义资源回退选项，DRA 在 `1.36` 中的升级都会对你有所帮助。下面我们来看看这
些新特性和进阶内容。

## 特性进阶

社区一直在努力稳定 DRA 的核心概念。在 Kubernetes `1.36` 中，多项备受期待的
特性已经进入 Beta 和稳定阶段。

### 优先级列表（稳定） {#prioritized-list}

硬件异构是大多数集群中的现实情况。借助
[Prioritized list](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#prioritized-list)
特性，你可以在请求设备时定义回退偏好。你无需将对特定设备型号的请求硬编码，而
是可以指定一个有序的偏好列表，例如“给我一块 H100，如果没有可用的，就回退到
A100”。调度器会按顺序评估这些请求，从而显著提升调度灵活性和集群利用率。

### 扩展资源支持（Beta） {#extended-resource}

随着 DRA 成为资源分配的标准，与传统系统打通差距就变得至关重要。DRA 的
[Extended resource](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#extended-resource)
特性允许用户通过 Pod 上传统的扩展资源方式来请求资源。这使得向 DRA 的过渡可以
循序渐进，也就是说，集群运维人员可以将集群迁移到 DRA，而让应用开发者按照自己
的节奏采用 `ResourceClaim` API。

### 可切分设备（Beta） {#partitionable-devices}

硬件加速器能力强大，而有时单个工作负载并不需要整台设备。
[Partitionable devices](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#partitionable-devices)
特性为 DRA 原生提供了支持：可根据工作负载需求，将物理硬件动态切分为更小的逻辑
实例，例如多实例 GPU。这使管理员能够在多个 Pod 之间安全且高效地共享昂贵的加
速器。

### 设备污点（Beta） {#device-taints}

正如你可以为 Kubernetes Node 添加污点一样，你也可以直接为特定 DRA 设备添加污
点。
[Device taints and tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#device-taints-and-tolerations)
让集群管理员能够更高效地管理硬件。你可以为故障设备添加污点，防止它们被分配给
普通申领，也可以为专门团队、特定工作负载和实验保留特定硬件。最终，只有具有匹
配容忍度的 Pod 才允许申领这些带污点的设备。

### 设备绑定状况（Beta） {#device-binding-conditions}

为了提升调度可靠性，Kubernetes 调度器可以使用
[Binding conditions](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#device-binding-conditions)
特性，在 Pod 所需的外部资源，例如可挂接设备或 FPGA，完全就绪之前，延迟将 Pod
提交到某个节点。通过显式地对资源就绪状态建模，这一特性能够防止过早分配导致 Pod
失败，从而确保部署过程更加稳健且可预测。

### 资源健康状态（Beta） {#device-health-monitoring}

对于运行在专用硬件上的工作负载来说，知道设备何时故障或变得不健康至关重要。借
助
[Resource health status](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#device-health-monitoring)，
Kubernetes 直接在 Pod 状态中暴露设备健康信息，为用户和控制器提供了关键的可见
性，以便快速识别并响应硬件故障。该特性还支持易于阅读的健康状态消息，使问题诊
断变得容易得多，而无需深入复杂的驱动日志。

## 新特性

除了稳定现有能力之外，`v1.36` 还引入了一些基础性的新特性，进一步扩展了 DRA 的
能力边界。这些特性目前都处于 Alpha 阶段，因此都受默认禁用的 feature gate 控制。

### 面向工作负载的 ResourceClaim 支持 {#workload-resourceclaims}

为了优化依赖严格拓扑调度的大规模 AI/ML 工作负载，
[ResourceClaim support for workloads](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#workload-resourceclaims)
特性使 Kubernetes 能够在大规模 Pod 集合之间无缝管理共享资源。通过将
`ResourceClaim` 或 `ResourceClaimTemplate` 与 `PodGroup` 关联起来，该特性消除
了此前的扩展性瓶颈，例如可共享某个申领的 Pod 数量限制，同时也减轻了专用编排器
手动管理申领的负担。

### 节点可分配资源 {#node-allocatable-resources}

为什么 DRA 只能用于外部加速器呢？在 `v1.36` 中，我们引入了使用 DRA API 管理
_节点可分配_ 基础设施资源，例如 CPU 和内存的首个迭代版本。通过 DRA 的
[Node allocatable resources](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#node-allocatable-resources)
特性，将 CPU 和内存分配纳入 DRA 的统一范畴后，用户就可以将 DRA 的高级放置能
力、NUMA 感知和优先级语义应用到标准计算资源上，从而为极细粒度的性能调优铺平
道路。

### DRA 资源可用性可见性 {#resource-pool-status}

集群管理员最常提出的需求之一，就是希望更好地了解硬件容量。全新的
[Resource pool status](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#resource-pool-status)
特性允许你查询 DRA 资源池中的设备可用性。通过创建
`ResourcePoolStatusRequest` 对象，你可以获得某个驱动所管理的每个资源池在某一时
刻的设备数量快照，包括总数、已分配、可用和不可用。这也使它能够更好地与仪表板
和容量规划工具集成。

### 属性的列表类型 {#list-type-attributes}

`ResourceClaim` 的约束求值机制已经调整，以便更好地处理标量值和列表值：

- `matchAttribute` 现在检查是否存在非空交集。
- `distinctAttribute` 则检查值是否两两不相交。

同时，CEL 中还引入了一个 `includes()` 函数，这使设备选择器在某个属性于标量表示
和列表表示之间变化时，仍然更容易继续正常工作。这个 `includes()` 函数仅在 DRA
上下文中的表达式求值时可用。

### 确定性设备选择 {#deterministic-device-selection}

Kubernetes 调度器现已更新，会基于资源池和 `ResourceSlice` 的名称，以字典序来评
估设备。这一变化使驱动能够主动影响调度过程，从而带来更高的吞吐量和更优的调度
决策。`ResourceSlice` 控制器工具包会自动生成名称，以反映驱动作者指定的精确设备
顺序。

### 容器中可发现的设备元数据 {#device-metadata}

运行在带有 DRA 设备节点上的工作负载，通常需要在不查询 Kubernetes API 的情况
下，发现其已分配设备的详细信息，例如 PCI 总线地址或网络接口配置。借助
[Device metadata](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/#device-metadata)，
Kubernetes 定义了一套标准协议，用于规定 DRA 驱动如何以带版本的 JSON 文件形
式，在众所周知的路径下向容器暴露设备属性。

使用
[DRA kubelet plugin library](https://pkg.go.dev/k8s.io/dynamic-resource-allocation/kubeletplugin)
构建的驱动可以透明地获得这一行为；它们只需要提供元数据，其余如文件布局、CDI
bind-mount、版本控制和生命周期管理，都由该库负责处理。这为应用提供了一种一
致、与驱动无关的方式来发现和使用设备元数据，从而无需再借助自定义控制器或通过
查询 `ResourceSlice` 对象属性来获取元数据。

## 下一步是什么？

这一版本引入了大量新的动态资源分配（DRA）特性，而且势头仍在持续增强。展望未
来，路线图将聚焦于推动现有特性走向 Beta 和稳定发布阶段，同时进一步夯实 DRA 的
性能、可扩展性和可靠性。在接下来的几个迭代周期中，一个关键优先事项将是与
_workload aware scheduling_ 和 _topology aware scheduling_ 的深度集成。

另一个重要目标，是推动用户从 Device Plugin 迁移到 DRA。无论你当前正在维护某个
驱动，还是刚开始探索这些可能性，你的意见都至关重要。与社区一起塑造下一代资源
管理能力，分享反馈，或者开始构建你的第一个 DRA 驱动程序。

## 参与其中

一个不错的起点，是加入 WG Device Management 的
[Slack 频道](https://kubernetes.slack.com/archives/C0409NGC1TK)
和[会议](https://docs.google.com/document/d/1qxI87VqGtgN7EAJlqVfxx86HGKEAc2A3SKru8nJHNkQ/edit?tab=t.0#heading=h.tgg8gganowxq)，
这些会议分别安排在适合 Americas/EMEA 和 EMEA/APAC 的时间段举行。

并非所有增强想法目前都已经作为 issue 进行跟踪，因此，如果你想提供帮助，或者你
自己也有一些想法，欢迎来和社区交流。这里在各个层面都有工作要做，从困难的核心
变更，到 `kubectl` 的易用性增强，其中一些工作也很适合新贡献者上手。

## AI-Infra 延伸阅读

- [DRA 总览文档](../../kubernetes/dra.md)
- [Kubernetes v1.36 DRA 的整体设计：从请求入口到调度、状态与拓扑](../2026-04-23/2026-04-23-kubernetes-v1.36-dra-ai-infra_zh.md)
- [Upstream: Kubernetes v1.33 DRA updates](https://kubernetes.io/blog/2025/05/01/kubernetes-v1-33-dra-updates/)
- [Upstream: Kubernetes v1.34: DRA gets even more powerful](https://kubernetes.io/blog/2025/09/01/kubernetes-v1-34-dra-updates/)
