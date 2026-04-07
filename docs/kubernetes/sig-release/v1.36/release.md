# Kubernetes v1.36 正式发布稿（精简版草案）

> 写作基线：截至 2026-03-31 的上游公开信息与 `kubernetes/sig-release#2958` 讨论内容。v1.36 计划发布时间为 2026-04-22（周三），正式发布当天请以 CHANGELOG 和 release notes 为准。

本文结构按“前瞻精简 + highlights 展开”组织：
- 前瞻里已经提到的内容，在这里做升级必读级别的精简提示。
- `#2958` 讨论中的重点功能作为正文主线，提供相对完整说明。

## 一、升级必读（来自 prerelease，精简版）

### 1) 弃用与移除

- `Service.spec.externalIPs`：v1.36 开始弃用并给出告警，计划 v1.43 移除。建议迁移到 `LoadBalancer`、`NodePort` 或 `Gateway API`。（KEP-5707）
- `gitRepo` 卷驱动：v1.36 起永久禁用且不可重新启用。建议改为 `initContainer`、镜像构建阶段打包或外部 `git-sync`。（KEP-5040）

### 2) 生态风险提示

- Ingress NGINX 已在 2026 年 3 月退役，不再提供后续修复和安全更新。现网可继续运行，但建议尽快完成迁移方案评估。

## 二、Highlights Discussion 重点功能（展开版）

### 重点一：Mutating Admission Policies 升级到 GA（KEP-3962）

过去很多团队依赖 mutating webhook 做策略注入、默认值补全和安全控制，但 webhook 体系本身有明显运维成本：需要额外部署与证书管理、故障会放大 API 请求路径风险、升级和排障链路也更长。对于多集群平台，这类“外置准入逻辑”通常是稳定性薄弱点之一。

v1.36 中，基于 CEL 的 Mutating Admission Policies 进入 GA，意味着“声明式、进程内”的变更准入能力进入稳定阶段。它与已 GA 的 Validating Admission Policy 形成闭环，让集群在“校验 + 变更”两个环节都能减少对外部 webhook 的硬依赖。对平台团队来说，最直接价值是把一部分高频、可声明化的准入逻辑收敛到 apiserver 内部能力，降低控制面外围组件复杂度。

落地上建议采用分层迁移：先从无副作用、纯字段变换的 webhook 规则迁入 CEL；再评估是否继续保留少量复杂 webhook（例如强依赖外部系统查询或复杂状态编排的场景）。这样可以在不牺牲策略能力的前提下，逐步换取更可控的稳定性与变更成本。

### 重点二：ServiceAccount Token 外部签名升级到 GA（KEP-740）

传统模式下，kube-apiserver 直接持有 ServiceAccount token 签名密钥，密钥生命周期与控制面节点绑定较深。对有合规要求或集中密钥管理要求的组织，这会带来审计、轮换、权限隔离上的治理压力。

KEP-740 在 v1.36 的稳定化价值，在于把签名能力标准化地委托给外部系统（如 HSM、云 KMS），让 Kubernetes 与企业既有密钥治理体系对齐。它并不只是“换个签名位置”，而是把密钥保护边界、轮换流程和审计责任从单集群节点层面提升到统一安全基础设施层面。

实施时建议重点关注三件事：第一，签名链路延迟和可用性对认证路径的影响；第二，外部签名服务故障时的降级和恢复流程；第三，密钥轮换演练与审计证据闭环。做完这三项验证，外部签名才能真正转化为生产收益而不仅是架构升级。

### 重点三：Volume Group Snapshot 面向 GA（KEP-3476）

单卷快照难以覆盖多卷应用的一致性恢复诉求：当数据库数据卷、日志卷、元数据卷之间存在写入顺序关系时，分别快照往往无法保证同一恢复点。对训练平台、状态型中间件和复杂事务应用，这个问题在故障恢复时尤为明显。

Volume Group Snapshot 的核心价值，是把“多个相关卷”作为一个逻辑组进行快照与恢复，目标是提供 crash-consistent 的恢复点。它依赖 CSI 侧的一组扩展 API，能力边界清晰，也更利于存储厂商和平台团队在统一接口下协作。

从平台实践看，这项能力最适合进入“备份恢复演练”而不仅是功能开关验证：建议把它纳入 RTO/RPO 目标校验，针对典型多卷工作负载做周期性恢复演练。只有把恢复链路跑通并量化结果，才能真正发挥该特性的业务价值。

## 三、其他 Highlights（每项一段）

### 1) 细粒度 Kubelet API 鉴权（KEP-2862，Stable）

该能力允许按请求类型（如 exec、logs、metrics、port-forward）进行更细粒度授权，而不是把 kubelet 端点访问作为粗粒度权限整体放开。它的实际意义是让节点侧接口更接近最小权限模型，降低“拿到一种权限即可过度访问”的风险。

### 2) DRA AdminAccess for ResourceClaims（KEP-5018，Stable）

该特性支持以特权模式创建 ResourceClaim，用于在设备已被占用时执行管理类任务（如健康检查、状态查看）。对共享加速器环境而言，这有助于把“运维可见性”与“业务占用路径”解耦，减少排障时对业务负载的干扰。

### 3) Constrained Impersonation（KEP-5284，Beta）

它允许发起模拟（impersonation）的一方主动将自身可用权限进一步收敛到子集，避免直接获得目标身份的完整权限视图。对多租户平台和审计敏感场景，这让模拟机制更适合纳入日常运维而非仅限特权操作。

### 4) IP/CIDR Validation Improvements（KEP-4858，Beta）

该改动收紧了非规范和歧义 IP/CIDR 写法的接受范围，减少不同实现间解释不一致引发的安全与互通问题。升级前建议先做配置巡检，清理历史遗留的“可解析但不规范”地址写法，避免在发布窗口触发阻塞。

### 5) statusz / flagz（KEP-4827、KEP-4828，Beta）

核心组件的 `/statusz` 与 `/flagz` 能力升级到 beta 且默认启用，使组件运行状态和关键配置暴露方式更一致。对平台可观测体系来说，这提升了控制面日常巡检和基线核对效率。

### 6) Mixed Version Proxy（KEP-4020，Beta）

该能力在版本偏斜场景下把请求转发到可处理该资源的 API Server，并提供更完整的聚合发现视图。它对“滚动升级中偶发 404/发现不一致”的缓解价值较高，适合作为升级窗口稳定性增强项来评估。

### 7) HPA Scale to Zero（KEP-2021，Alpha）

HPA 在 object/external metrics 场景支持从 0 到非 0 的伸缩能力，为事件驱动和低频工作负载提供更激进的成本优化空间。由于仍处于 Alpha，建议仅在边界可控场景试点，并明确冷启动与指标时效的观测基线。

### 8) Workload Aware Scheduling（WAS）相关方向（SIG Scheduling）

SIG Scheduling 在 #2958 中将 WAS 作为当前重点方向，关联 KEP 包括 5832、5732、5729、5710、5547、4671。该方向的核心目标是让调度器更理解“工作负载级”约束（如 PodGroup、拓扑与抢占协同），对 AI/批处理集群的价值尤其明显。

### 9) Declarative Validation（KEP-5073，GA 方向）

除 Mutating Admission Policy 外，Declarative Validation 的 GA 方向也值得作为 v1.36 重点叙事：它把“声明式校验”能力推进到更稳定阶段，帮助平台将部分分散在 webhook 或自定义控制器中的校验逻辑收敛到统一的 API 语义层。

### 10) DRA 1.36 打包更新（稳定化 + 新能力并行）

DRA 在 v1.36 的信号不是单点特性，而是多项能力并行推进：包括 prioritized list、extended resource、partitionable devices、device taints、binding conditions，以及 workload / native resource / visibility 等方向。对 AI 和异构算力平台，更建议将其作为一组“资源编排能力跃迁”来评估。

### 11) User Namespaces（GA）落地实践

User Namespaces 进入 GA 后，容器内用户与宿主机用户隔离的工程可用性更强，适合在多租户场景中与 RuntimeClass、seccomp、SELinux/AppArmor 等机制配套落地，形成“默认最小权限 + 分层隔离”的节点安全基线。

### 12) 控制面可扩展性改进（KEP-5647、KEP-5866）

controller staleness mitigation 与 server-side sharded list/watch 组合起来，分别针对控制器端陈旧状态影响与 apiserver 大规模 list/watch 压力做优化。两者的共同价值是把“控制面在大集群下的稳定性”从经验调优转向可机制化改进。

### 13) SELinux 兼容准备（升级风险前置）

虽然相关 breaking changes 主题常被放在后续版本窗口讨论，但其核心动作需要在 v1.36 周期前置完成：尽早盘点现有工作负载的 SELinux 相关假设与策略依赖，避免升级窗口内集中暴露兼容性问题。

> 说明：EvictionRequest API、HPA fallback external metrics、Deployment Pod Replacement Policy 相关稿件当前仍以占位探索为主，暂不作为本版 release 主线展开。

## 四、建议的升级动作

1. 全量扫描清单与集群对象，完成 `externalIPs`、`gitRepo` 使用点盘点和迁移计划。
2. 对入口层做维护状态审计，尽快推进 Ingress NGINX 迁移路线。
3. 以 staging 为主验证准入策略、API Machinery 与调度相关改动，再逐步推进生产。
4. 对多卷状态型业务执行组快照恢复演练，量化 RTO/RPO 并形成发布闸门。
5. 升级当天对照最终 `CHANGELOG-1.36.md` 与 release notes 做差异复核。

## 五、参考链接

- <https://kubernetes.io/blog/2026/03/30/kubernetes-v1-36-sneak-peek/>
- <https://github.com/kubernetes/sig-release/discussions/2958>
- <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/README.md>
- <https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md>
- <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-notes/release-notes-draft.md>
- <https://kep.k8s.io/5707>
- <https://kep.k8s.io/5040>
- <https://kep.k8s.io/3962>
- <https://kep.k8s.io/740>
- <https://kep.k8s.io/3476>
