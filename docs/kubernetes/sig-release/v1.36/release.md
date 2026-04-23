# Kubernetes v1.36 正式发布：DRA 加速成熟，WAS 迈向原生工作负载调度

2026 年 4 月 23 日（北京时间周四），Kubernetes v1.36 正式发布。上游官方发布博客统计显示，本版本包含 70 项增强：18 项进入 Stable，25 项进入 Beta，25 项进入 Alpha，另有 2 项弃用或移除。

与前几个版本类似，v1.36 仍然延续了“稳定化 + 可扩展性 + 资源编排演进”的主线。对 AI Infra 团队而言，本版本最值得关注的是 DRA 设备管理继续扩展、Workload Aware Scheduling 开始补齐原生批处理/训练调度能力，以及组快照、大规模 list/watch、节点侧大列表流式返回等稳定性能力持续推进。

## 发布主题和 Logo

v1.36 的发布主题是 `ハル（Haru）`。Haru 在日语中同时关联“春”“晴空”和“远方”等意象，官方发布叙事也围绕“晴れに翔け”（飞向晴空）展开。

本版本 Logo 由 Natsuho Ide（GitHub ID: `avocadoneko`）创作，灵感来自葛饰北斋《富岳三十六景》中的《凯风快晴》（又名《赤富士》）。Kubernetes 船舵标志悬于赤富士之上，并以 “v1.36” 与“三十六景”形成呼应。

## 重要系列

### DRA 1.36 一系列更新

v1.36 的 DRA 不是单个特性毕业，而是一组资源编排能力同时推进。和 AI/GPU 平台最相关的变化包括：`Prioritized List` 进入 Stable，`Extended Resource`、`Partitionable Devices`、`Device Taints`、`Binding Conditions`、`Resource Health Status` 等进入 Beta；同时还开启了 Workload 级 ResourceClaim、面向 CPU/内存的 Native Resources、资源池可见性和 ResourceSlice 属性 List 类型等新方向。

这些能力组合起来，带来的直接价值是：

1. 更灵活的资源回退与调度，提高稀缺 GPU、TPU、NIC 等设备利用率。
2. 更可观测的设备健康、状态和容量视图，降低训练任务异常定位和恢复成本。
3. 从加速卡扩展到 CPU/内存等原生资源的统一编排路径，为大规模 AI/批处理资源管理打基础。

DRA 相关 KEP 可按能力分组理解：

- [KEP-3695](https://kep.k8s.io/3695)：让节点监控和本地组件通过 kubelet PodResources API 查询 Pod 通过 DRA 分配到的资源。
- [KEP-4680](https://kep.k8s.io/4680)：把 Device Plugin/DRA 设备健康状态暴露到 Pod Status。
- [KEP-4815](https://kep.k8s.io/4815)：支持 GPU MIG、TPU 等可分区或多主机逻辑设备。
- [KEP-4816](https://kep.k8s.io/4816)：允许 ResourceClaim 声明按优先级排列的多种可接受设备选择。
- [KEP-4817](https://kep.k8s.io/4817)：允许 DRA driver 在 ResourceClaim 状态中写入已分配设备状态和标准化网络信息。
- [KEP-5004](https://kep.k8s.io/5004)：让 `nvidia.com/gpu: 2` 这类 extended resource 请求可由 DRA driver 满足。
- [KEP-5007](https://kep.k8s.io/5007)：支持需要异步 attach 的资源在外部资源 ready 后再进行 Pod binding。
- [KEP-5018](https://kep.k8s.io/5018)：提供受控的 privileged ResourceClaim 模式，用于健康检查、诊断和监控。
- [KEP-5055](https://kep.k8s.io/5055)：允许 DRA driver 或管理员给设备打 taint，并由 workload 通过 toleration 明确接受。
- [KEP-5075](https://kep.k8s.io/5075)：支持多个 ResourceClaim 按容量份额共享同一底层设备。
- [KEP-5304](https://kep.k8s.io/5304)：把 DRA driver 提供的设备元数据以标准路径暴露给容器。
- [KEP-5491](https://kep.k8s.io/5491)：让 ResourceSlice 的设备属性支持 typed list，表达 NUMA、PCIe root 等多值拓扑关系。
- [KEP-5517](https://kep.k8s.io/5517)：当 CPU/Memory 等核心资源也由 DRA 管理时，统一 scheduler 资源记账，避免重复计算导致超卖。
- [KEP-5677](https://kep.k8s.io/5677)：为排障和容量规划提供 DRA 资源池剩余容量视图。
- [KEP-5729](https://kep.k8s.io/5729)：让 Workload/PodGroup 级对象引用 DRA ResourceClaim/ResourceClaimTemplate。

### WAS 与 Gang Scheduling 继续推进

WAS（Workload Aware Scheduling）是 SIG Scheduling 当前重点方向，关联 KEP 包括 [KEP-4671](https://kep.k8s.io/4671)、[KEP-5832](https://kep.k8s.io/5832)、[KEP-5732](https://kep.k8s.io/5732)、[KEP-5729](https://kep.k8s.io/5729)、[KEP-5710](https://kep.k8s.io/5710)、[KEP-5547](https://kep.k8s.io/5547)。它的核心目标是让调度器理解“工作负载级”约束，而不是只按单个 Pod 做局部最优调度。

通过将 Workload 重构为静态模板、引入独立 PodGroup 运行时 API，并在 kube-scheduler 中新增 PodGroup 调度周期，Kubernetes 开始具备以“整组工作负载”为单位进行原子调度的能力，也就是 Gang Scheduling。对 AI/ML 和大规模批处理来说，这能减少“部分 Pod 已占资源但整体任务无法启动”的资源浪费。

v1.36 还补充了拓扑感知调度、工作负载感知抢占、面向 PodGroup 的 DRA ResourceClaim 支持，并启动 Job 控制器集成。把这些变化合并看，WAS 正在把过去依赖外部批调度系统的部分能力逐步带回 Kubernetes 原生调度路径。

### WAS 拓扑感知调度（KEP-5732，Alpha）

WAS 拓扑感知调度的目标是在同一拓扑域内协同放置整组 Pod，而不是逐个 Pod 独立选择节点，从而减少跨机架、跨可用区通信放大和工作负载碎片化。该能力由 `TopologyAwareWorkloadScheduling` feature gate 控制，v1.36 中默认关闭。

调度框架上，v1.36 为 PodGroup 调度新增 `placementGenerate` 与 `placementScore` 两个扩展点，并引入或扩展了 `TopologyPlacement`、`NodeResourcesFit`、`PodGroupPodsCount` 等插件。API 使用上，PodGroup 可通过 `schedulingConstraints.topology[].key` 声明拓扑约束；v1.36 仅支持单个 topology constraint。

生产建议是先在拓扑敏感场景灰度验证，例如分布式训练、GPU + NIC 强绑定任务，重点观察跨域流量、任务完成时延和 pending 行为。

## 安装/升级注意事项

### API 与对象兼容性

- `Service.spec.externalIPs` 在 v1.36 开始弃用并给出告警，计划在 v1.43 移除其实现（字段本身不会移除）。建议迁移到 `LoadBalancer`、`NodePort` 或 `Gateway API`（KEP-5707）。
- `gitRepo` 卷驱动在 v1.36 起永久禁用且不可重新启用。建议改为 `initContainer` 拉取、镜像构建阶段打包或外部 `git-sync`（KEP-5040）。

### 生态与运行时风险

- Ingress NGINX 已于 2026 年 3 月退役，不再提供后续修复和安全更新。现网虽可继续运行，但建议尽快完成迁移路线评估。
- 建议利用 v1.36 升级窗口盘点 SELinux volume label 与 `seLinuxChangePolicy` 使用方式。该能力在 v1.36 进入 Stable，但如果多个特权/非特权 Pod 共享同一卷，错误配置仍可能带来后续版本的兼容风险。
- 部分 Beta 功能虽然已具备较高可用性，但 feature gate 或 beta API 默认状态仍需逐项确认。升级前建议在 staging 和灰度环境系统性验证。

## GA 和稳定的功能

GA（General Availability）代表功能进入稳定阶段，也常称 Stable。v1.36 的核心信号是：准入能力进一步完善，身份签名治理能力增强，节点与资源侧能力持续成熟。

### Mutating Admission Policies（KEP-3962）

过去很多团队依赖 mutating webhook 做策略注入、默认值补全和安全控制，但 webhook 体系本身有明显运维成本：需要额外部署与证书管理、故障会放大 API 请求路径风险，升级和排障链路也更长。对于多集群平台，这类“外置准入逻辑”通常是稳定性薄弱点之一。

v1.36 中，基于 CEL 的 Mutating Admission Policies 进入 GA，意味着“声明式、进程内”的变更准入能力进入稳定阶段。它与已 GA 的 Validating Admission Policy 形成闭环，让集群在“校验 + 变更”两个环节都能减少对外部 webhook 的硬依赖。

落地上建议采用分层迁移：先从无副作用、纯字段变换的 webhook 规则迁入 CEL；再评估是否继续保留少量复杂 webhook，例如强依赖外部系统查询或复杂状态编排的场景。

### ServiceAccount Token 外部签名（KEP-740）

传统模式下，kube-apiserver 直接持有 ServiceAccount token 签名密钥，密钥生命周期与控制面节点绑定较深。对有合规要求或集中密钥管理要求的组织，这会带来审计、证书轮换、权限隔离上的治理压力。

KEP-740 的价值在于把签名能力标准化地委托给外部系统，如 HSM 或云 KMS，让 Kubernetes 与企业既有密钥治理体系对齐。它并不只是“换个签名位置”，而是把密钥保护边界、轮换流程和审计责任从单集群节点层面提升到统一安全基础设施层面。

### Volume Group Snapshot（KEP-3476）

单卷快照难以覆盖多卷应用的一致性恢复诉求：当数据库数据卷、日志卷、元数据卷之间存在写入顺序关系时，分别快照往往无法保证同一恢复点。对训练平台、状态型中间件和复杂事务应用，这个问题在故障恢复时尤为明显。

Volume Group Snapshot 的核心价值，是把“多个相关卷”作为一个逻辑组进行快照与恢复，目标是提供 crash-consistent 的恢复点。它依赖 CSI 侧的一组扩展 API，能力边界清晰，也更利于存储厂商和平台团队在统一接口下协作。对训练恢复和复杂状态型业务来说，建议把它纳入 RTO/RPO 演练，而不是只做功能开关验证。

### 细粒度 Kubelet API 鉴权（KEP-2862）

该能力允许按请求类型，如 `exec`、`logs`、`metrics`、`port-forward`，进行更细粒度授权，而不是把 kubelet 端点访问作为粗粒度权限整体放开。它的实际意义是让节点侧接口更接近最小权限模型，降低“拿到一种权限即可过度访问”的风险。

### DRA AdminAccess for ResourceClaims（KEP-5018）

该特性支持以特权模式创建 ResourceClaim，用于在设备已被占用时执行健康检查、状态查看等管理类任务。对共享加速器环境而言，这有助于把“运维可见性”与“业务占用路径”解耦，减少排障时对业务负载的干扰。使用时需要确保 privileged ResourceClaim 只授权给确实需要的运维或平台身份。

### User Namespaces（GA）

User Namespaces 仅适用于 Linux 节点。其核心价值是将容器内的 UID/GID 与宿主机身份解耦：容器内看起来是 `root`（UID 0）的进程，在宿主机侧映射为非特权高位 UID，从而显著降低容器逃逸后的主机提权风险。

使用方式保持与 Beta 阶段一致：在 Pod 或 PodTemplate 中设置 `hostUsers: false` 即可启用，无需改造镜像。启用后，类似 `CAP_NET_ADMIN` 这类能力会变为用户命名空间内的“局部能力”，可管理容器内资源但不会直接影响主机。配合 Linux 内核的 ID-mapped mounts，卷挂载不再依赖大规模 `chown`，在大卷场景下可明显改善启动与恢复效率。

### Node Log Query（Windows）

Node Log Query 在 v1.36 进入 Stable，意味着通过 kubelet `/logs` 查询节点服务日志的能力进一步固化。该能力覆盖 Linux 与 Windows 节点，并可处理系统日志提供器与文件日志路径。

从生产使用角度，仍需注意配置边界：能力稳定化不等于默认全面开放。是否开放系统日志处理仍依赖 kubelet 配置项 `enableSystemLogHandler`。建议将其作为“故障排查开关”纳入运维手册，而不是长期默认暴露。

### SELinux Volume Label Changes（KEP-1710）

v1.36 中 SELinux volume label 相关优化进入 Stable，可以减少递归 relabel 带来的挂载延迟，并让 `seLinuxChangePolicy` 成为更明确的工作负载配置项。升级前需要确认现有 Deployment、StatefulSet、DaemonSet 或自定义资源中的 PodTemplate 是否隐式依赖旧行为；对于共享卷场景，尤其要避免特权与非特权 Pod 的标签策略互相影响。

### 更新总览

- [KEP-3962 Mutating Admission Policies（Stable）](https://kep.k8s.io/3962)
- [KEP-740 ServiceAccount Token 外部签名（Stable）](https://kep.k8s.io/740)
- [KEP-1710 SELinux Volume Label Changes（Stable）](https://kep.k8s.io/1710)
- [KEP-3476 Volume Group Snapshot（Stable）](https://kep.k8s.io/3476)
- [KEP-2862 细粒度 Kubelet API 鉴权（Stable）](https://kep.k8s.io/2862)
- [KEP-3695 DRA PodResources API 可观测性（Stable）](https://kep.k8s.io/3695)
- [KEP-5018 DRA AdminAccess for ResourceClaims（Stable）](https://kep.k8s.io/5018)
- [KEP-4816 DRA Prioritized List（Stable）](https://kep.k8s.io/4816)

## 进入 Beta 阶段的功能

Beta 阶段功能通常已具备较高可用性，建议先在 staging 与灰度环境系统性验证，再分批引入生产。部分 Beta 功能仍可能涉及 feature gate 或 beta API 默认状态，需要在升级前逐项确认。

### Constrained Impersonation（KEP-5284）

Constrained Impersonation 引入受限身份模拟机制，通过在 impersonation 流程中增加额外授权检查，使模拟者不仅需要具备“模拟目标身份”的权限，还必须具备“在该身份下执行具体操作”的权限，从而避免获得目标身份的完整权限能力。

该机制将传统的“全权限继承”模型转变为“受控委托”，更符合最小权限原则，也让 impersonation 更适合多租户平台和审计敏感的日常运维场景。

### IP/CIDR Validation Improvements（KEP-4858）

该改动收紧了非规范和歧义 IP/CIDR 写法的接受范围，减少不同实现间解释不一致引发的安全与互通问题。升级前建议先做配置巡检，清理历史遗留的“可解析但不规范”地址写法，避免在发布窗口触发阻塞。

### statusz / flagz（KEP-4827、KEP-4828）

核心组件的 `/statusz` 与 `/flagz` 能力升级到 Beta 且默认启用，使组件运行状态和关键配置暴露方式更一致。对平台可观测体系来说，这提升了控制面日常巡检和基线核对效率。

### Mixed Version Proxy（KEP-4020）

Mixed Version Proxy 也被称为未知版本互操作代理。该能力在版本偏斜场景下把请求转发到可处理该资源的 API Server，并提供更完整的聚合发现视图。它对“滚动升级中偶发 404/发现不一致”的缓解价值较高，适合作为升级窗口稳定性增强项来评估。

### Controller Staleness Mitigation（KEP-5647）

KEP-5647 主要解决“控制器基于陈旧 cache 做决策”的问题。Kubernetes controller 通常通过 informer cache 读取对象状态，而这个 cache 来自 apiserver 的 watch stream，本质上是最终一致的；在大规模、高 churn 或 apiserver/watch 延迟场景下，controller 本地视图可能落后于真实状态，进而导致重复 reconcile、错误删除 Pod、错误扩缩容或无意义写入。

该 KEP 的核心机制，是让 controller 能感知 informer cache 当前推进到的 resourceVersion，并在关键写入后记录对应 resourceVersion。下一轮 reconcile 前，如果本地 cache 尚未追上前一次写入，就跳过本轮处理并 requeue，等 cache 追上后再继续。它把 stale read 风险转化为可检测、可等待、可回退的控制器机制。

### DRA Beta 能力集合

DRA 在 v1.36 的 Beta 能力集合包括 extended resources、partitionable devices、device taints、binding conditions、resource health status 等方向。对 AI 与异构算力平台，更建议将其作为一组“资源编排能力跃迁”来评估，而不是只看单个 feature gate。

### 更新总览

- [KEP-5284 Constrained Impersonation](https://kep.k8s.io/5284)
- [KEP-4858 IP/CIDR Validation Improvements](https://kep.k8s.io/4858)
- [KEP-4827 statusz](https://kep.k8s.io/4827)
- [KEP-4828 flagz](https://kep.k8s.io/4828)
- [KEP-4020 Mixed Version Proxy](https://kep.k8s.io/4020)
- [KEP-5647 Controller Staleness Mitigation](https://kep.k8s.io/5647)
- [KEP-4680 DRA Resource Health Status](https://kep.k8s.io/4680)
- [KEP-4815 DRA Partitionable Devices](https://kep.k8s.io/4815)
- [KEP-5004 DRA Extended Resources](https://kep.k8s.io/5004)
- [KEP-5007 DRA Binding Conditions](https://kep.k8s.io/5007)
- [KEP-5055 DRA Device Taints](https://kep.k8s.io/5055)

## 进入 Alpha 阶段的功能

Alpha 功能默认关闭，建议仅在边界可控场景试点，并明确可观测基线、回滚路径和启停条件。WAS 和 DRA 的部分能力已经在前文单独介绍，这里补充几项对平台团队更有价值的 Alpha 能力。

### HPA Scale to Zero（KEP-2021）

HPA 在 Object/External metrics 场景支持从 0 到非 0 的伸缩能力，为事件驱动和低频工作负载提供更激进的成本优化空间。它不适用于 CPU/Memory 这类依赖运行中 Pod 的资源指标，而是更适合队列长度、外部事件积压量等可以在副本数为 0 时仍然被观测到的指标。试点时要重点关注冷启动时延、指标时效、误扩缩容保护和回滚路径。

### Server-side Sharded List/Watch（KEP-5866）

KEP-5866 主要解决“apiserver list/watch 流量无法真正水平分片”的问题。在大集群中，Pod 等核心资源事件量很高，很多控制器或观测组件希望通过多副本水平扩展来分摊压力；但传统 client-side sharding 下，每个副本仍然要从 apiserver 接收完整 watch stream，再在本地反序列化、过滤并丢弃不属于自己的对象。

该 KEP 提出在 LIST/WATCH 请求中加入服务端分片能力，例如通过 shard selector 指定 shard key 和 hash range，由 apiserver 在源头过滤对象和事件，使每个 watcher 只收到自己负责的 shard。它的效果是把“业务侧假分片”升级为“API Server 原生真分片”，降低 watch fan-out、客户端反序列化和无效事件处理成本。

### CRI List Streaming（KEP-5825）

CRI List Streaming 把类似的大列表问题放到节点侧处理：它为 kubelet 与容器运行时之间的 List 类调用引入服务端流式返回能力，避免一次性返回大量容器或镜像信息时造成 kubelet 内存峰值和响应延迟。节点上 Pod、容器和镜像数量越多，这类“单次大响应”的压力越明显。

### Native Histogram Support（KEP-5808）

v1.36 引入 Kubernetes 指标的 Native Histogram 支持，让控制面组件可以导出更高分辨率的延迟分布数据。相比传统 Prometheus histogram 依赖固定 buckets 的方式，Native Histogram 使用更稀疏、动态的表达方式，在不显著增加手工 bucket 维护成本的情况下，提升对长尾延迟和突发抖动的观察能力。对平台团队来说，这项能力最直接服务于 apiserver 等核心组件的 SLI/SLO 建设。

### Manifest Based Admission Control Config（KEP-5793）

Manifest Based Admission Control Config 是 v1.36 引入的 Alpha 能力，由 `ManifestBasedAdmissionControlConfig` feature gate 控制，主要作用于 kube-apiserver。它不是新增一种准入策略语言，而是为 admission webhook 和 CEL 准入策略提供一种 API 外部、manifest 化的配置来源：通过 `AdmissionConfiguration` 中的 `staticManifestsDir`，API server 可以在启动时从本地目录加载准入配置，并在运行中监听文件变化后重新加载。

它解决的是 API 型准入配置的治理问题：避免关键准入配置在集群启动早期尚未创建或尚未生效，也降低其被 Kubernetes API 删除、修改或在 etcd 异常时不可用的风险。它和 Mutating Admission Policies 的关注点不同：MAP 关注“如何声明准入变更逻辑”，而 Manifest Based Admission Control Config 关注“准入配置从哪里加载、何时生效、如何作为平台级基线被保护”。由于仍处于 Alpha，且存在 HA 配置一致性、回滚和监控限制，建议先用于测试集群和配置基线验证。

### 更新总览

- [KEP-2021 HPA Scale to Zero](https://kep.k8s.io/2021)
- [KEP-5866 Server-side Sharded List/Watch](https://kep.k8s.io/5866)
- [KEP-5825 CRI List Streaming](https://kep.k8s.io/5825)
- [KEP-5808 Native Histogram Support](https://kep.k8s.io/5808)
- [KEP-5793 Manifest Based Admission Control Config](https://kep.k8s.io/5793)
- [KEP-5732 WAS Topology Aware Scheduling](https://kep.k8s.io/5732)

## 删除和废弃功能

### Service `externalIPs` 开始弃用（KEP-5707）

v1.36 起，`Service.spec.externalIPs` 已进入弃用周期并提供告警信号，计划在 v1.43 移除其实现。建议提前完成对象清单扫描与迁移计划，避免后续版本进入移除窗口时形成被动整改。

### `gitRepo` 卷驱动永久禁用（KEP-5040）

v1.36 起 `gitRepo` 卷驱动不可重新启用。建议统一切换至 `initContainer` 拉取、镜像构建阶段打包或外部 `git-sync` 方案，减少运行时拉取代码的安全与稳定性风险。

## 建议的升级动作

1. 全量扫描清单与集群对象，完成 `externalIPs`、`gitRepo` 使用点盘点和迁移计划。
2. 对入口层做维护状态审计，尽快推进 Ingress NGINX 迁移路线。
3. 盘点 SELinux volume label、`seLinuxChangePolicy` 与共享卷场景，避免升级后集中暴露标签策略问题。
4. 在 staging 中验证 Mutating Admission Policies、Constrained Impersonation、statusz/flagz 与 Mixed Version Proxy，再分批推进生产。
5. 对多卷状态型业务执行组快照恢复演练，量化 RTO/RPO 并形成发布闸门。
6. 针对 DRA 设备健康、分区设备、taints/tolerations、extended resources 做灰度验证，重点观察调度成功率、设备故障定位和容量视图。
7. 针对 WAS/PodGroup/Gang Scheduling 的训练和批处理场景建立试点评估，重点观察资源空占、拓扑通信和 pending 行为。
8. 大规模集群可先评估 Controller Staleness Mitigation、Server-side Sharded List/Watch、CRI List Streaming 与 Native Histogram 对控制面和节点稳定性的收益。

## DaoCloud 近期社区贡献

DaoCloud 在 Kubernetes 社区持续参与。近期新增 Kueue 文档 Approver 李信和要海峰（CNCF 大使），Kueue 中文官方网站也已经上线：<https://kueue.sigs.k8s.io/zh-cn/docs/>。

在 vLLM 社区，范宝发和卢传佳成为 vLLM Semantic Router 项目的 Committer。卢传佳还孵化了新项目 [clawwork](https://github.com/clawwork-ai/clawwork)，作为 OpenClaw 的客户端，支持多会话并行任务管理、多 Agent 协作编排，以及本地优先的任务/文件/上下文持久化工作流。

DaoCloud 近期还在孵化云原生项目 [MatrixHub](https://github.com/matrixhub-ai/matrixhub)，面向企业级私有化大模型资产（模型、数据与版本）统一管理与分发基础设施。

## 活动预告

- 6 月 18 - 19 日：KubeCon + CloudNativeCon India 2026，印度孟买。
- 7 月 29 - 30 日：KubeCon + CloudNativeCon Japan 2026，日本横滨。
- 9 月 8 - 9 日：KubeCon + CloudNativeCon China 2026，中国上海。CFP 截止 5 月 3 日，同期举办 PyTorchCon、OpenInfra Summit、MCP Dev Summit。
- 11 月 9 - 12 日：KubeCon + CloudNativeCon North America 2026，美国盐湖城。
- 11 月：KCD 2026 杭州。

## 发行说明

更多发布细节请参考 Kubernetes 主库和官方博客：

- Kubernetes v1.36 官方发布博客：<https://kubernetes.io/blog/2026/04/22/kubernetes-v1-36-release/>
- Kubernetes v1.36 CHANGELOG：<https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md>
- Kubernetes v1.36 release notes draft：<https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-notes/release-notes-draft.md>

## 历史文档

- [Kubernetes 1.35 发布！安装/升级变化巨大，新特性 Gang Scheduling 重磅来袭！](https://github.com/DaoCloud-OpenSource/docs/blob/main/kubernetes/sig-release/v1.35/release.md)

## 参考

1. Kubernetes v1.36 官方发布博客 <https://kubernetes.io/blog/2026/04/22/kubernetes-v1-36-release/>
2. Kubernetes v1.36 Sneak Peek <https://kubernetes.io/blog/2026/03/30/kubernetes-v1-36-sneak-peek/>
3. Kubernetes v1.36 主题讨论 <https://github.com/kubernetes/sig-release/discussions/2958>
4. Kubernetes v1.36 发布分支说明 <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/README.md>
5. Kubernetes v1.36 变更日志 <https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md>
6. Kubernetes v1.36 Release Notes Draft <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-notes/release-notes-draft.md>
7. 微信公众号文章：Kubernetes v1.36 正式发布：DRA 加速成熟，WAS 迈向原生工作负载调度 <https://mp.weixin.qq.com/s/U4uBpXIWG9AzwwqDzjEc7A>
8. KEP-5707 <https://kep.k8s.io/5707>
9. KEP-5040 <https://kep.k8s.io/5040>
10. KEP-3962 <https://kep.k8s.io/3962>
11. KEP-740 <https://kep.k8s.io/740>
12. KEP-3476 <https://kep.k8s.io/3476>
