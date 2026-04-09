# Kubernetes v1.36 即将发布：升级风险前置，准入与资源编排能力持续演进

2026 年 4 月 22 日（周三），Kubernetes v1.36 计划正式发布。

本文基于截至 2026-04-07 的上游公开信息与 `kubernetes/sig-release#2958` 讨论内容整理，正式发布当天请以 `CHANGELOG-1.36.md` 与 release notes 为准。

与前几个版本类似，v1.36 仍然延续了“稳定化 + 可扩展性 + 资源编排演进”的主线。本文按 v1.35 发布稿结构整理，先给出升级必读，再展开重点能力。

## 发布主题和 Logo

截至 2026-04-07，v1.36 的官方发布主题与 Logo 仍以 SIG Release 正式公告为准。本文先聚焦升级风险与关键特性，主题视觉素材可在正式发布后补充。

## 安装/升级注意事项

### API 与对象兼容性

- `Service.spec.externalIPs` 在 v1.36 开始弃用并给出告警，计划在 v1.43 移除。建议迁移到 `LoadBalancer`、`NodePort` 或 `Gateway API`（KEP-5707）。
- `gitRepo` 卷驱动在 v1.36 起永久禁用且不可重新启用。建议改为 `initContainer`、镜像构建阶段打包或外部 `git-sync`（KEP-5040）。

### 生态与运行时风险

- Ingress NGINX 已于 2026 年 3 月退役，不再提供后续修复和安全更新。现网虽可继续运行，但建议尽快完成迁移路线评估。
- 建议在升级窗口前完成 SELinux 相关盘点，识别现有工作负载对标签与策略的隐式依赖，避免在发布窗口集中暴露兼容问题。

## GA 和稳定的功能

GA（General Availability）代表功能进入稳定阶段，可作为生产可用能力评估。v1.36 的核心信号是：准入能力进一步内建化，身份签名治理能力增强，节点与资源侧能力持续成熟。

### Mutating Admission Policies 升级到 GA（KEP-3962）

过去很多团队依赖 mutating webhook 做策略注入、默认值补全和安全控制，但 webhook 体系本身有明显运维成本：需要额外部署与证书管理、故障会放大 API 请求路径风险、升级和排障链路也更长。对于多集群平台，这类“外置准入逻辑”通常是稳定性薄弱点之一。

v1.36 中，基于 CEL 的 Mutating Admission Policies 进入 GA，意味着“声明式、进程内”的变更准入能力进入稳定阶段。它与已 GA 的 Validating Admission Policy 形成闭环，让集群在“校验 + 变更”两个环节都能减少对外部 webhook 的硬依赖。对平台团队来说，最直接价值是把一部分高频、可声明化的准入逻辑收敛到 apiserver 内部能力，降低控制面外围组件复杂度。

落地上建议采用分层迁移：先从无副作用、纯字段变换的 webhook 规则迁入 CEL；再评估是否继续保留少量复杂 webhook（例如强依赖外部系统查询或复杂状态编排的场景）。这样可以在不牺牲策略能力的前提下，逐步换取更可控的稳定性与变更成本。

### ServiceAccount Token 外部签名升级到 GA（KEP-740）

传统模式下，kube-apiserver 直接持有 ServiceAccount token 签名密钥，密钥生命周期与控制面节点绑定较深。对有合规要求或集中密钥管理要求的组织，这会带来审计、轮换、权限隔离上的治理压力。

KEP-740 在 v1.36 的稳定化价值，在于把签名能力标准化地委托给外部系统（如 HSM、云 KMS），让 Kubernetes 与企业既有密钥治理体系对齐。它并不只是“换个签名位置”，而是把密钥保护边界、轮换流程和审计责任从单集群节点层面提升到统一安全基础设施层面。

实施时建议重点关注三件事：第一，签名链路延迟和可用性对认证路径的影响；第二，外部签名服务故障时的降级和恢复流程；第三，密钥轮换演练与审计证据闭环。做完这三项验证，外部签名才能真正转化为生产收益而不仅是架构升级。

### Volume Group Snapshot 面向 GA（KEP-3476）

单卷快照难以覆盖多卷应用的一致性恢复诉求：当数据库数据卷、日志卷、元数据卷之间存在写入顺序关系时，分别快照往往无法保证同一恢复点。对训练平台、状态型中间件和复杂事务应用，这个问题在故障恢复时尤为明显。

Volume Group Snapshot 的核心价值，是把“多个相关卷”作为一个逻辑组进行快照与恢复，目标是提供 crash-consistent 的恢复点。它依赖 CSI 侧的一组扩展 API，能力边界清晰，也更利于存储厂商和平台团队在统一接口下协作。

从平台实践看，这项能力最适合进入“备份恢复演练”而不仅是功能开关验证：建议把它纳入 RTO/RPO 目标校验，针对典型多卷工作负载做周期性恢复演练。只有把恢复链路跑通并量化结果，才能真正发挥该特性的业务价值。

### 细粒度 Kubelet API 鉴权（KEP-2862，Stable）

该能力允许按请求类型（如 `exec`、`logs`、`metrics`、`port-forward`）进行更细粒度授权，而不是把 kubelet 端点访问作为粗粒度权限整体放开。它的实际意义是让节点侧接口更接近最小权限模型，降低“拿到一种权限即可过度访问”的风险。

### DRA AdminAccess for ResourceClaims（KEP-5018，Stable）

该特性支持以特权模式创建 ResourceClaim，用于在设备已被占用时执行管理类任务（如健康检查、状态查看）。对共享加速器环境而言，这有助于把“运维可见性”与“业务占用路径”解耦，减少排障时对业务负载的干扰。

### User Namespaces（GA）落地实践

User Namespaces 在 v1.36 进入 GA，且该能力仅适用于 Linux 节点。其核心价值是将容器内的 UID/GID 与宿主机身份解耦：容器内看起来是 `root`（UID 0）的进程，在宿主机侧映射为非特权高位 UID，从而显著降低容器逃逸后的主机提权风险。

落地方式仍然保持 Beta 期一致：在 Pod（或 PodTemplate）中设置 `hostUsers: false` 即可启用，无需改造镜像。启用后，类似 `CAP_NET_ADMIN` 这类能力会变为用户命名空间内的“局部能力”，可管理容器内资源但不会直接影响主机。配合 Linux 内核的 ID-mapped mounts，卷挂载不再依赖大规模 `chown`，在大卷场景下可明显改善启动与恢复效率。

### Node Log Query 进入稳定阶段（SIG Windows 补充）

根据 `#2958` 在 2026-03-31 的补充，Node Log Query 在 v1.36 进入 stable，意味着通过 kubelet `/logs` 查询节点服务日志的能力进一步固化。该能力覆盖 Linux 与 Windows 节点，并可处理系统日志提供器与文件日志路径。

从生产使用角度，仍需注意配置边界：能力稳定化不等于默认全面开放。是否开放系统日志处理仍依赖 kubelet 配置项 `enableSystemLogHandler`。建议将其作为“故障排查开关”纳入运维手册，而不是长期默认暴露。

### 更新总览

- [KEP-3962 Mutating Admission Policies（GA）](https://kep.k8s.io/3962)
- [KEP-740 ServiceAccount Token 外部签名（GA）](https://kep.k8s.io/740)
- [KEP-3476 Volume Group Snapshot（GA 方向）](https://kep.k8s.io/3476)
- [KEP-2862 细粒度 Kubelet API 鉴权（Stable）](https://kep.k8s.io/2862)
- [KEP-5018 DRA AdminAccess for ResourceClaims（Stable）](https://kep.k8s.io/5018)
- [KEP-5073 Declarative Validation（GA 方向）](https://kep.k8s.io/5073)

## 进入 Beta 阶段的功能

Beta 阶段功能通常已具备较高可用性，建议先在 staging 与灰度环境系统性验证，再分批引入生产。

### Constrained Impersonation（KEP-5284，Beta）

它允许发起模拟（impersonation）的一方主动将自身可用权限进一步收敛到子集，避免直接获得目标身份的完整权限视图。对多租户平台和审计敏感场景，这让模拟机制更适合纳入日常运维而非仅限特权操作。

### IP/CIDR Validation Improvements（KEP-4858，Beta）

该改动收紧了非规范和歧义 IP/CIDR 写法的接受范围，减少不同实现间解释不一致引发的安全与互通问题。升级前建议先做配置巡检，清理历史遗留的“可解析但不规范”地址写法，避免在发布窗口触发阻塞。

### statusz / flagz（KEP-4827、KEP-4828，Beta）

核心组件的 `/statusz` 与 `/flagz` 能力升级到 beta 且默认启用，使组件运行状态和关键配置暴露方式更一致。对平台可观测体系来说，这提升了控制面日常巡检和基线核对效率。

### Mixed Version Proxy（KEP-4020，Beta）

该能力在版本偏斜场景下把请求转发到可处理该资源的 API Server，并提供更完整的聚合发现视图。它对“滚动升级中偶发 404/发现不一致”的缓解价值较高，适合作为升级窗口稳定性增强项来评估。

### 控制面可扩展性改进（KEP-5647、KEP-5866）

`controller staleness mitigation` 与 `server-side sharded list/watch` 组合起来，分别针对控制器端陈旧状态影响与 apiserver 大规模 list/watch 压力做优化。两者的共同价值是把“大集群控制面稳定性”从经验调优转向机制化改进。

### DRA 1.36 打包更新（稳定化 + 新能力并行）

DRA 在 v1.36 的信号不是单点特性，而是多项能力并行推进：包括 `prioritized list`、`extended resource`、`partitionable devices`、`device taints`、`binding conditions`，以及 workload/native resource/visibility 等方向。对 AI 与异构算力平台，更建议将其作为一组“资源编排能力跃迁”来评估。

### SIG Node 在 #2958 的新增重点：DRA 与节点能力并进

根据 `#2958` 在 2026-04-02 的补充，SIG Node 强调 v1.36 的 DRA 不是单一功能升级，而是“多条能力线并行推进”：包括可分区设备、资源健康状态、扩展资源路径等。对平台侧的直接意义是，资源调度策略可以从“是否可分配”进一步走向“按健康度、按粒度、按回退策略分配”。

同一批次补充里还强调了若干节点与运行时能力的成熟度提升，包括 User Namespaces、PSI 相关能力、OCI 卷源，以及 kubelet 侧针对大规模容器场景的 CRI list streaming 和 Memory QoS 行为调整。将这些点合并看待，更准确的解读是：v1.36 在“节点可扩展性 + 资源隔离精细化”方向上形成了联动改进，而不只是单点特性毕业。

### 更新总览

- [KEP-5284 Constrained Impersonation](https://kep.k8s.io/5284)
- [KEP-4858 IP/CIDR Validation Improvements](https://kep.k8s.io/4858)
- [KEP-4827 statusz](https://kep.k8s.io/4827)
- [KEP-4828 flagz](https://kep.k8s.io/4828)
- [KEP-4020 Mixed Version Proxy](https://kep.k8s.io/4020)
- [KEP-5647 Controller Staleness Mitigation](https://kep.k8s.io/5647)
- [KEP-5866 Server-side Sharded List/Watch](https://kep.k8s.io/5866)

## 进入 Alpha 阶段的功能

Alpha 功能默认关闭，建议仅在边界可控场景试点，并明确可观测基线、回滚路径和启停条件。

### HPA Scale to Zero（KEP-2021，Alpha）

HPA 在 object/external metrics 场景支持从 0 到非 0 的伸缩能力，为事件驱动和低频工作负载提供更激进的成本优化空间。由于仍处于 Alpha，建议仅在边界可控场景试点，并明确冷启动与指标时效的观测基线。

### Workload Aware Scheduling（WAS）相关方向（SIG Scheduling）

SIG Scheduling 在 `#2958` 中将 WAS 作为当前重点方向，关联 KEP 包括 5832、5732、5729、5710、5547、4671。该方向的核心目标是让调度器更理解“工作负载级”约束（如 PodGroup、拓扑与抢占协同），对 AI/批处理集群价值尤其明显。

### 更新总览

- [KEP-2021 HPA Scale to Zero](https://kep.k8s.io/2021)
- [KEP-5832 Workload Aware Scheduling](https://kep.k8s.io/5832)
- [KEP-5732 WAS 相关增强](https://kep.k8s.io/5732)
- [KEP-5729 WAS 相关增强](https://kep.k8s.io/5729)
- [KEP-5710 WAS 相关增强](https://kep.k8s.io/5710)
- [KEP-5547 WAS 相关增强](https://kep.k8s.io/5547)
- [KEP-4671 Gang Scheduling 基础能力](https://kep.k8s.io/4671)

> 说明：EvictionRequest API、HPA fallback external metrics、Deployment Pod Replacement Policy 相关稿件当前仍以占位探索为主，暂不作为本版 release 主线展开。

## 删除和废弃功能

### Service `externalIPs` 开始弃用（KEP-5707）

v1.36 起，`Service.spec.externalIPs` 已进入弃用周期并提供告警信号。建议提前完成对象清单扫描与迁移计划，避免后续版本进入移除窗口时形成被动整改。

### `gitRepo` 卷驱动永久禁用（KEP-5040）

v1.36 起 `gitRepo` 卷驱动不可重新启用。建议统一切换至 `initContainer` 拉取、镜像构建阶段打包或外部 `git-sync` 方案，减少运行时拉取代码的安全与稳定性风险。

## 建议的升级动作

1. 全量扫描清单与集群对象，完成 `externalIPs`、`gitRepo` 使用点盘点和迁移计划。
2. 对入口层做维护状态审计，尽快推进 Ingress NGINX 迁移路线。
3. 以 staging 为主验证准入策略、API Machinery 与调度相关改动，再逐步推进生产。
4. 对多卷状态型业务执行组快照恢复演练，量化 RTO/RPO 并形成发布闸门。
5. 升级当天对照最终 `CHANGELOG-1.36.md` 与 release notes 做差异复核。

## DaoCloud 社区贡献

本节建议在正式发布前补充 DaoCloud 社区在 v1.36 周期内的贡献数据（如 SIG 角色、关键 PR/KEP 参与、演讲与维护工作），以保持与往期发布稿结构一致。

## 发行说明

上述内容为 v1.36 发布前精简稿，更多发布细节请以正式发布当日版本说明为准：

- Kubernetes v1.36 CHANGELOG：<https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md>
- Kubernetes v1.36 release notes draft：<https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-notes/release-notes-draft.md>

## 历史文档

- [K8s 1.35 发布！安装/升级变化巨大，新特性 Gang Scheduling 重磅来袭！](https://github.com/DaoCloud-OpenSource/docs/blob/main/kubernetes/sig-release/v1.35/release.md)

## 参考

1. Kubernetes v1.36 Sneak Peek <https://kubernetes.io/blog/2026/03/30/kubernetes-v1-36-sneak-peek/>
2. Kubernetes v1.36 主题讨论 <https://github.com/kubernetes/sig-release/discussions/2958>
3. Kubernetes v1.36 发布分支说明 <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/README.md>
4. Kubernetes v1.36 变更日志 <https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md>
5. Kubernetes v1.36 Release Notes Draft <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-notes/release-notes-draft.md>
6. KEP-5707 <https://kep.k8s.io/5707>
7. KEP-5040 <https://kep.k8s.io/5040>
8. KEP-3962 <https://kep.k8s.io/3962>
9. KEP-740 <https://kep.k8s.io/740>
10. KEP-3476 <https://kep.k8s.io/3476>
