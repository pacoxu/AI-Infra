---
status: Active
maintainer: pacoxu
date: 2026-10-21
last_updated: 2026-10-21
tags: kubernetes, openkruise, agent-sandbox, traffic-policy, security-profile, pool-autoscaler, ai-infrastructure
canonical_path: docs/blog/2026-10-21/2026-10-21-openkruise-agents-v0.6.0_zh.md
source_urls:
  - https://openkruise.io/blog/2026/10/07/agents-v0.6.0
  - https://github.com/openkruise/agents/releases
  - https://openkruise.io/kruiseagents/user-manuals/security/traffic-access-control
  - https://openkruise.io/kruiseagents/user-manuals/poolautoscaler
  - https://openkruise.io/kruiseagents/user-manuals/sandbox-update
  - https://github.com/openkruise/agents
  - https://openkruise.io/zh/kruiseagents/
---

# OpenKruise Agents v0.6.0：沙箱终于自带数据面

[OpenKruise Agents v0.6.0](https://openkruise.io/blog/2026/10/07/agents-v0.6.0)
的官方博文日期是 **2026-10-07**，GitHub Release 为
[`v0.6.0`](https://github.com/openkruise/agents/releases)。自 v0.3.0 以来合并
283 个 PR，新增 27 位贡献者。

v0.3.0 回答的是：Sandbox 交给 Agent 之后，怎么升级、怎么变配、怎么归属。路线图
当时留下两个承诺——用 `TrafficPolicy` / `SecurityProfile` 做网络治理，以及把平台
凭证从 Agent 代码里移走。v0.6.0 把这两件事做成了一等组件，并补上围绕它们的运维
机制。可以记成四项能力：

1. **4/7 层访问控制与凭证注入**：目的地可达性、单次请求检查、MCP 工具级 ACL、从 Secret 改写出向请求。
2. **`SandboxUpdateOps`**：`CheckpointRestore` 保住 rootfs；`stateFilter` 把休眠实例纳入批量升级。
3. **`PoolAutoscaler`**：用可用容量水位和 Cron 改写预热池副本数。
4. **自动休眠唤醒**：探针识别闲置、按时刻表提前唤醒、入口流量唤醒。

合在一起是三类平台价值：安全加固、声明式运维、闲置与预热池的成本。

## 架构：从工作负载层到自带数据面

v0.3.0 还是工作负载控制器。v0.6.0 把流量检查、策略下发和身份凭证收进项目自己的
组件，组件从四个变成六个：

| 组件 | v0.6.0 里的角色 |
| --- | --- |
| `sandbox-manager` | 无状态北向 API（E2B 兼容），管生命周期、配额、路由与 traffic token |
| `sandbox-controller` | 调和 `Sandbox` / `SandboxSet` / `SandboxClaim` 与预热池，带 admission webhook，并驱动自动休眠唤醒 |
| `sandbox-gateway` | Envoy Go filter 数据面。入口做 host/path、访问令牌和流量唤醒；出口做策略约束的 L7 出向 |
| `traffic-control-plane` | 新增。`istiod` 向网关和 Pod 内代理下发 xDS；出口策略执行器（EPE）做 L7、MCP ACL 和凭证注入 |
| `agent-runtime` | Sidecar，提供 E2B envd 兼容的命令、文件和端口（49983）操作 |
| `traffic-proxy` | 新增。Pod 内 L4 出向执行点 |

出向路径是固定的：

```text
Sandbox 应用容器
  → traffic-proxy（Pod 内 L4 捕获，命中拒绝就地丢弃）
  → 按出口路由选中的 egress-gateway
  → Envoy ext_proc
  → EPE（L7 / MCP ACL / 凭证注入）
  → 目标服务，或返回阻断响应
```

两件后果决定了后面所有功能怎么落地。出向不再由 Pod 自己放行：流量在 Pod 内被
捕获，经过出口网关，由能看见完整请求的策略引擎做决定。入口网关可以唤醒
Sandbox，所以「流量唤醒」不需要集群外再跑一个轮询器。职责也是刻意拆开的：L4
拒绝在到达网关之前就被丢掉，L7 不能推翻 L4 的拒绝结论；直通、不经网关的流量
根本到不了 EPE。

CRD 从 v0.3.0 的 6 个增加到 12 个。v0.6.0 新标出来的是 `PoolAutoscaler`、
`TrafficPolicy`、`GlobalTrafficPolicy`、`SecurityProfile`、`GlobalSecurityProfile`。
`SandboxUpdateOps` 在 v0.3.0 就已经存在。`Commit` 仍在 feature gate 后面。完整名单：

| CRD | 范围 | 作用 |
| --- | --- | --- |
| `Sandbox` / `SandboxSet` / `SandboxTemplate` / `SandboxClaim` | Namespace | 单实例、同构预热池、不可变模板、领取与领取后处理 |
| `Checkpoint` / `Commit` | Namespace | 运行时快照；把可写层存成新镜像（`Commit` 为 Alpha） |
| `SandboxUpdateOps` | Namespace | 对已领取 Sandbox 做一次性批量升级 |
| `PoolAutoscaler` | Namespace | 预热池容量与 Cron |
| `TrafficPolicy` / `GlobalTrafficPolicy` | Namespace / Cluster | L3/L4 出入向目的地控制，以及集群级 L4 基线 |
| `SecurityProfile` / `GlobalSecurityProfile` | Namespace / Cluster | L7 请求检查、MCP ACL、凭证注入、审计，以及集群级 L7 基线 |

层次是：集群基线、租户 Profile、单个 Sandbox 的内联网络规则。

北向 API 继续兼容 E2B，兼容矩阵写明了边界：`pause` 同步且完全兼容；`create` 上
网络访问控制可用，创建路径的 MCP 集成仍未完成；`network` 支持 `allowOut` /
`denyOut` / `rules`，`egressProxy` 和 `maskRequestHost` 会被直接拒绝，而不是静默
忽略。预签名上传下载、logs、metrics、生命周期事件和 Volumes 尚未支持。

## 网络访问控制与 Token

这块回答三个问题：Sandbox 可以访问什么、谁可以访问 Sandbox、上游 API Key 握在
谁手里。

### L4：目的地可不可达

`TrafficPolicy` 用 label 选中调用方 Pod，持有一份有序出口规则。Peer 可以是
`fqdn`、`cidr`、`service` 或 `workload`，多个 Peer 之间是或。三条语义比字段名
更要紧：

- 策略一旦选中 Pod，未命中任何 allow 的出向流量即拒绝。挂上即白名单。
- 缺少 Peer 的规则会被编译器跳过，不构成默认拒绝。`to` 写错会静默削弱策略。
- 必须放行集群 DNS Service。否则解析失败，所有 FQDN 规则看起来都像坏了。

```yaml
apiVersion: agents.kruise.io/v1alpha1
kind: TrafficPolicy
metadata:
  name: sandbox-egress
spec:
  selector:
    matchLabels:
      app: traffic-sample
  egress:
    rules:
      - action: allow
        to:
          - service: {name: kube-dns, namespace: kube-system}
      - action: allow
        to:
          - fqdn: api.example.com
      - action: reject
        ports: [{protocol: TCP, port: 443}]
        to:
          - cidr: 10.0.0.0/8
```

`GlobalTrafficPolicy` 是同一模型的集群级基线。

### L7：这一次请求允许做什么

`SecurityProfile` 匹配 HTTP 请求再施加动作。`match` 子句之间是或，同一子句里
填了的字段是与，`domains` 必填。动作里 `block` 和 `bypass` 会终止后续规则；
`mcpToolPolicy`、`headerManipulation`、`tokenTransformation`、`audit` 不终止。

评估顺序按 `spec.priority` 从小到大（默认 1000），再比创建时间、名字、命名空间。
全局 Profile 和命名空间 Profile 走同一顺序，完全打平则全局在前。匹配不是
第一条命中即停，只有终止性动作才截断链条。同一条规则内部的动作顺序固定为
`bypass`、`block`、`mcpToolPolicy`、`headerManipulation`、`tokenTransformation`，
与 YAML 键的书写顺序无关。

对 Agent 工作负载，价值最高的是 SSRF 防护：被提示注入的代码会去碰内网和云元数据
端点。集群基线用较低的 `priority` 排在租户 Profile 之前：

```yaml
apiVersion: agents.kruise.io/v1alpha1
kind: GlobalSecurityProfile
metadata:
  name: cluster-baseline
spec:
  selector:
    matchLabels: {app: traffic-sample}
  priority: 50
  rules:
    - name: deny-metadata-endpoint
      match:
        - domains:
            - metadata.internal
            - "*.internal.company.com"
      actions:
        block:
          statusCode: 403
          body: '{"error":"access to internal services is forbidden"}'
```

`GlobalSecurityProfile` 不能设置 `metadata.namespace`。

### MCP 工具级 ACL

域名级管控盖不住「这个 MCP Server 上哪一个工具能被调用」。`mcpToolPolicy` 只处理
JSON-RPC 的 `tools/call`，精确匹配 `params.name`；`tools/list` 和 `initialize`
会放行。规则按文档顺序、首次命中即停。白名单要写 `defaultAction: deny`：
`defaultAction: allow` 时，读不出 body 或叫不出工具名的调用按设计放行。执行器会
缓冲完整 body，超过 8 MiB、JSON-RPC batch、不支持的编码都退回 `defaultAction`。
文档列出的 MCP 协议版本是 `2025-06-18`、`2025-11-25`、`2026-07-28`。

### 凭证注入

凭证放在 Kubernetes Secret 里。出口代理按请求解析，在请求即将离开集群时改写
出站头。工作负载和 Agent 代码只看得到自己的占位请求头。

```yaml
apiVersion: agents.kruise.io/v1alpha1
kind: SecurityProfile
metadata:
  name: example-api-credentials
  namespace: agent-demo
spec:
  selector:
    matchLabels: {app: agent}
  rules:
    - name: inject-example-api-key
      match:
        - domains: [api.example.com]
          schemes: [https]
          paths: [{type: Prefix, value: /v1/}]
      actions:
        tokenTransformation:
          type: ApiKey
          failStrategy: Block
          credentialRef:
            secret:
              name: example-api-credentials
          apiKey:
            targetHeaders:
              names: [authorization]
            value:
              template: "Bearer {{ .Token }}"
```

解析发生在代理侧，所以凭证不会出现在 Pod Spec、环境变量或 Sandbox metadata 里。
轮换 Secret 不需要重启 Sandbox。`failStrategy` 默认 `Block`：凭证缺失时失败关闭。
`secret` 与 `credentialProvider` 只能设一个。`headerManipulation` 的值是明文，
不能拿来放凭证。

不想写 CRD 的团队可以用 E2B SDK 表达网络意图，前提是 Sandbox 跑了 `traffic-proxy`。
不对称点要记住：`allowOut` 接受 IP、CIDR 和具体 FQDN（通配符会被拒绝），
`denyOut` 只接受 IP 和 CIDR。主机名过滤因此是「允许名单 + `0.0.0.0/0` 拒绝」，
并且 allow 优先于 deny。`rules` 只携带按域名的 header 变换，本身不授予可达性。

### 护栏

管控只覆盖经网关路由的流量。HTTPS 深度检查还要 TLS 终结、签名 CA 和工作负载信任
这条链。以 root 运行，或具备 `NET_ADMIN` / `SYS_ADMIN` 的容器可以绕过 Pod 内
ACL，需要和 Kubernetes NetworkPolicy、主机防火墙或云安全组一起用。伪造的 `Host`
头可以躲开 L4 匹配，这正是 L7 Profile 存在的原因。TrafficProxy 占用
15001、15006、15012、15020、15021、15090，并以 UID/GID 1337 运行。EPE 是每条经
网关请求上的一跳，Deployment 要单独容量规划。单 Sandbox 内联规则
（`agents.kruise.io/security-rules`）排在 selector 匹配的 Profile 之后；编译失败会
保留上一份规则或变成未强制，由 `epe_profile_stale`、`epe_profile_unenforced`
（`scope="pod"`）暴露。

中文发布稿里的网关性能图标注为理论评估上限，图中数字未随正文给出，这里不转写。
运行中看网关日志的 `duration_ms`，并关注 502 与丢包。

同篇中文稿给出的生产口径，本仓库未独立复现：MiniMax（MaxClaw）称自定义模板预热
加 MicroVM 做到 20–40ms 实例供给、最高约 15,000 沙箱/分钟；Kimi（月之暗面）称高峰
数万并发、后台 Pod 十万级、分钟级千节点扩容；理想汽车称 MicroVM 隔离加东西向 /
南北向流量管控下约 800 名员工常态使用，并规划到数万乃至数十万 Agent。当作厂商
口径阅读，落地以自己的压测为准。

## SandboxUpdateOps：保住 rootfs，并升级休眠实例

v0.3.0 的 `SandboxUpdateOps` 只有 `Recreate`：销毁并重建 Pod，内存、IP 和 rootfs
可写层都丢，状态只能靠 `preUpgrade` / `postUpgrade` 钩子搬到外部存储。v0.6.0
补了两件分开的事，不要混成一种模式：

| 模式 | rootfs | 内存 | IP | 业务镜像 |
| --- | --- | --- | --- | --- |
| `Recreate`（默认） | 丢失 | 丢失 | 变化 | 可以更换 |
| `CheckpointRestore` | 升级前做检查点，升级后恢复 | 丢失 | 变化 | 不能更换 |

`CheckpointRestore` 用镜像灵活性换文件系统连续性，适合滚动 `agent-runtime` /
`traffic-proxy` 这类 Sidecar，或改 env、resources、volumes 等非镜像字段。业务容器
镜像在这种模式下一改，恢复出来的 rootfs 就会被丢掉。业务镜像要变、又要留状态时，
仍然是 `Recreate` 加钩子：`preUpgrade` 备份到对象存储或 NAS，`postUpgrade` 拉回来。

休眠实例是另一条路径。v0.6.0 之前，`SandboxUpdateOps` 只碰 `Running` 或
`Upgrading`，休眠池对批量升级不可见，版本会漂。`stateFilter.states` 写入
`Paused` 之后，控制器逐个唤醒、升级，若 `spec.paused` 仍为 true 再休眠回去。
升级结束时集群形态与开始时一致，休眠池不会被一次升级叫醒成一笔账单。更换业务
镜像的休眠升级走默认 `Recreate`，与 `CheckpointRestore` 是两套约束。

## PoolAutoscaler：预热池容量变成策略

预热池是亚秒级 Claim 的原因，也是深夜无人使用时账单仍在涨的原因。
`PoolAutoscaler` 只改写 `SandboxSet.spec.replicas`。它不采集业务指标，不预测流量，
也不自己创建或删除 Pod。

`capacityPolicy.targetAvailable: "50%"` 表示把可用（未被领取）Sandbox 维持在总副本
的一半，用来吸收突发 Claim。水位按 `ceil(平均副本 × (target ± tolerance)%)` 计算，
`tolerance` 默认 `10%`。扩容稳定窗口宜短（示例 60 秒）、缩容宜长（示例 300 秒）：
短缺用户立刻能感觉到，缓慢缩容则不会。

Cron 在已知波峰之前触发，优先级高于容量反馈，并且不受容量稳定窗口约束，仍被
`minReplicas` / `maxReplicas` 夹住。`timezone` 要显式写；五段 cron，最多 20 条且
名字唯一。校验失败返回 HTTP 422。`spec.suspend: true` 暂停伸缩而不删除对象。删掉
`PoolAutoscaler` 后，`SandboxSet.spec.replicas` 停在最后一次写入的值，池子不会自己
缩回去。

几个会写错的约束：`targetAvailable: "100%"` 会让池子只增不减；`tolerance` 必须严格
小于 `targetAvailable`；百分比目标要求 `minReplicas` 至少为 1；稳定窗口为 60 到
3600 秒。绝对水位下 `target + downTolerance` 不能超过 `minReplicas`，否则策略永远
触发不了缩容。

中文发布稿还把 Claim 时的原地内存变配写成配套降本手段：预热池按较小统一规格持有，
`SandboxClaim` 领取时再对运行中的主容器做 CPU / 内存原地变配。这依赖 Kubernetes
1.33+ 的原地 Pod 变配，以及默认开启的 `SandboxInPlaceResourceResize`。交付会比
「池里已经是目标规格」略慢，仍然快于冷启动。官方 CRD 说明里，`SandboxClaim` 的
领取后处理本来就包括换镜像、挂卷和原地变配。

未领取的预热 Sandbox 会跑探针，但不参与自动休眠决策。池子容量归
`PoolAutoscaler`，闲置休眠归已领取实例。

## 自动休眠唤醒

在 Kubernetes 看来，一个有活跃会话的已领取 Sandbox，和一个几小时没人用的
Sandbox，对象形态一样。自动休眠唤醒把差异做成探针条件，再据此行动。配置在
`SandboxSet` 的 `probes` 与 `autoPausePolicy` 上。

探针只支持 `exec`，不支持 HTTP 或 TCP。命令不会自动套 shell，要自己写 `sh -c`。
退出码 0 得到 `status: "True"`，stdout 进入 condition message。失败或超时永远不
触发休眠或唤醒。

- **闲置休眠**：例如 Active 探针打印 `inactive`，`messageRegex` 持续匹配超过
  `thresholdDuration` 即休眠。`thresholdDuration: 0` 表示第一次报闲置就休眠。
  窗口要按探针周期叠加估算：探针内部若已用 15 分钟无活动作为判定，再加 10 分钟
  阈值和 30 秒周期，实际休眠大约落在最后一次真实活动之后 25 分钟。待休眠写入
  `status.schedules`，`reason: probedIdle`。
- **定时唤醒**：Cron 探针打印下一次激活时间。`timeFormat` 为 `unix`（正整数秒，
  默认）或带时区的 RFC 3339。`leadTime` 默认 5 分钟，可以为 0，不能为负。毫秒时间戳
  必须先除以 1000；业务本地时间要在探针里换成带时区的值再输出。没有待执行任务时
  打印 `none`，控制器不创建唤醒计划。
- **入向流量唤醒**：休眠后的第一个经网关请求会唤醒 Sandbox。需要网关打开
  `enable-wake-on-traffic`；`wake-timeout-seconds` 默认 60，超时调用方收到
  `503 sandbox wake failed`。E2B 侧对应
  `lifecycle={"on_timeout": "pause", "auto_resume": True}`。`commands.run` 和
  `files.write` 同样会触发唤醒。

真实节点上的探针还依赖已安装的 OpenKruise（kruise-daemon）和
`KruiseIntegration`。否则探针条件停在 `Unknown`，自动休眠不会触发。虚拟 kubelet
节点不受这一条影响。`AutoPauseController` 在 `sandbox-controller` 上默认开启。

三条运行时行为：

1. 请求必须通过鉴权。未授权返回 401，Sandbox 保持休眠。流量唤醒不是无需认证的门铃。
2. 唤醒成功可以伴随这次调用失败。触发唤醒的请求可能返回 503。检查
   `Sandbox.status.phase` 再重试。
3. 预热池里尚未领取的 Sandbox 仍属于 SandboxSet，对它的请求会得到
   `502 healthy sandbox not found`。

## 相对 v0.6.0 之前

| | v0.6.0 之前 | v0.6.0 |
| --- | --- | --- |
| 安全 | 出向是 Pod 自己的事；提示注入可以打到内网、云元数据和任意 MCP 工具；上游 API Key 要交给 Agent 运行时 | L3/L4 白名单、L7 检查、MCP 工具白名单、集群级 `Global*` 基线；凭证在出口代理从 Secret 解析，轮换无需重启；流量访问令牌改为短时轮换 JWT |
| 运维 | 休眠实例对批量升级不可见；池容量靠 `kubectl scale` 定时任务；闲置识别是脚本 | `stateFilter` 覆盖 `Paused`；`CheckpointRestore` 保留 rootfs；`PoolAutoscaler` 声明容量；闲置识别变成探针 |
| 成本 | 已领取 Sandbox 无论有没有人用都在烧 CPU；预热池按全天峰值持有 | 闲置实例休眠，按时刻表或首个请求唤醒；Cron 在低谷缩池；休眠池升级不会把池子整池叫醒 |

## 下一阶段

官方路线强调和既有开源项目协作，而不是再做一套封闭快照或身份栈：

- 与 Kata 社区基于 Kubernetes 1.37 的 `PodCheckpoint` API 做开源 Checkpoint，减少对特定平台快照后端的依赖。
- 在现有按需挂载框架上接入 MinIO 等开源存储。
- 与 Keycloak 一类开源身份系统对接，让平台认证落到已有身份提供方。

项目完全在开放社区构建。GitHub：<https://github.com/openkruise/agents>。
文档：<https://openkruise.io/zh/kruiseagents/>。钉钉群号 `23330762`。中文社区例会
为周四 19:30（GMT+8）；官方英文页同时写了 bi-weekly 与 Every Thursday，排期以社区
当前公告为准。

---

*整理自 OpenKruise 官方博文、用户手册与中文发布稿。客户规模与网关性能为项目口径，
未在本仓库复现。API 细节以 [v0.6.0 博文](https://openkruise.io/blog/2026/10/07/agents-v0.6.0)
和 [文档站](https://openkruise.io/kruiseagents/) 为准。*
