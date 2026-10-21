---
status: Active
maintainer: pacoxu
date: 2026-10-21
last_updated: 2026-10-21
tags: agent-sandbox, openkruise, mxc, strands-box, ack, ai-infrastructure
canonical_path: agent-infra/sandbox-control-planes-zh.md
source_urls:
  - https://openkruise.io/blog/2026/10/07/agents-v0.6.0
  - https://github.com/openkruise/agents
  - https://blogs.windows.com/windowsdeveloper/2026/10/07/microsoft-execution-containers-policy-driven-containment-for-ai-agents/
  - https://github.com/microsoft/mxc
  - https://aws.amazon.com/blogs/opensource/introducing-strands-box-ai-agent-sandboxes-powered-by-dogwood/
  - https://github.com/strands-agents/box
  - https://help.aliyun.com/zh/ack/product-overview/ack-agent-identity
  - https://help.aliyun.com/zh/agent-sandbox/user-guide/manage-agent-sandbox-egress-traffic
  - https://help.aliyun.com/zh/cs/ack-agent-sec-scanner
---

# Agent 沙箱控制面（2026-10）

2026-10-07 前后，沙箱讨论从「把代码关进容器」转到「策略在工作负载外面、按条件放行」。下面四层不要互相替换。

| 层 | 代表 | 回答的问题 |
| --- | --- | --- |
| 本机策略 | [MXC](https://github.com/microsoft/mxc)、[Strands Box](https://github.com/strands-agents/box) | 开发者机器上，这一次动作在什么条件下允许 |
| Kubernetes 数据面 | [openkruise/agents](https://github.com/openkruise/agents) v0.6.0 | 集群里一批 Sandbox 的出站、凭证、预热池和休眠 |
| 托管安全面 | ACK / ACS Agent Sandbox 容器版 | 在上述数据面上加云身份、巡检、护栏和内核证据 |
| 隔离运行时 | gVisor、Kata、Firecracker | 不可信代码和宿主机之间的边界 |

生产检验：打开 Sandbox，里面不该有长期 AK。有的话，安全性就押在模型不把密钥打进日志。

## OpenKruise Agents v0.6.0

官方博文日期 2026-10-07。自 v0.3.0 起合并 283 个 PR，新增 27 位贡献者。v0.3.0 留下的两个承诺——网络治理，以及凭证离开 Agent 代码——在这一版变成一等组件。

组件从四个变成六个。新增 `traffic-control-plane`（xDS 与出口策略执行器 EPE）和 `traffic-proxy`（Pod 内 L4）。出向路径是：应用容器 → `traffic-proxy`（命中拒绝就地丢弃）→ egress-gateway → Envoy ext_proc → EPE（L7、MCP ACL、凭证注入）。L7 不能推翻 L4 的拒绝。不经网关的流量到不了 EPE。入口网关可以唤醒 Sandbox，所以流量唤醒不需要集群外轮询器。

CRD 从 6 个增加到 12 个。v0.6.0 新标出的是 `PoolAutoscaler`、`TrafficPolicy`、`GlobalTrafficPolicy`、`SecurityProfile`、`GlobalSecurityProfile`。`SandboxUpdateOps` 在 v0.3.0 就有。`Commit` 仍在 feature gate 后。

**网络。** `TrafficPolicy` 挂上即白名单：未命中 allow 的出向被拒绝。缺少 Peer 的规则会被编译器跳过，`to` 写错会静默削弱策略。必须放行集群 DNS，否则 FQDN 规则看起来全部失效。`SecurityProfile` 里只有 `block` 和 `bypass` 终止后续规则。MCP 白名单要写 `defaultAction: deny`；`tools/list` 和 `initialize` 会放行。凭证放在 Secret 里，代理在请求离开集群时改写头，`failStrategy` 默认 `Block`。轮换 Secret 不必重启 Sandbox。

护栏：管控只覆盖经网关的流量。root 或 `NET_ADMIN` / `SYS_ADMIN` 可以绕过 Pod 内 ACL，要配 NetworkPolicy 或安全组。伪造 `Host` 可以躲开 L4，所以还要 L7 域名规则。E2B 北向仍部分兼容：`pause` 同步完成；`egressProxy` 和 `maskRequestHost` 会被直接拒绝。

**升级。** `CheckpointRestore` 只保留 rootfs，内存和 IP 仍会变，而且不能改业务镜像；业务镜像变更走默认 `Recreate`。`stateFilter` 把 `Paused` 纳入批量升级，若 `spec.paused` 仍为 true 就再休眠回去。这两件事不要混成一种模式。

**容量与休眠。** `PoolAutoscaler` 只改写 `SandboxSet.spec.replicas`，不采集业务指标。扩容窗口宜短、缩容宜长。Cron 优先于容量反馈，仍被 min/max 夹住。删掉 Autoscaler 后副本数停在最后一次写入。自动休眠的探针只有 `exec`；失败或超时不触发休眠或唤醒。流量唤醒必须先通过鉴权，未授权返回 401 且保持休眠。真实节点上的探针还要 OpenKruise（kruise-daemon）和 `KruiseIntegration`。

中文发布稿里的 MiniMax、Kimi、理想汽车规模，以及网关性能图，都是厂商口径，本仓库未复现。

## MXC 与 Strands Box

两份公告都在 2026-10-07。共同前提是：agent 不能成为它自己的安全权威。

策略可以截在三层。微虚拟机看得到的多半是 TLS 密文和块设备读写，适合「流量必须走网关」，不适合「这次是不是支付」。系统调用看得见路径和主机，看不见 MCP 工具名。语义层把 shell、Python、MCP 和网络收进策略引擎，能写时序和跨动作规则，受信计算基也因此变大。

| 产品 | 隔离 | 策略 | 状态 |
| --- | --- | --- | --- |
| Strands Box | macOS Seatbelt | Dogwood，默认拒绝，`forbid` 覆盖 `permit` | Apache-2.0，developer preview，仅 macOS 15+ / Apple silicon |
| MXC | 进程、会话、WSL、实验性微 VM | 一份 JSON：文件、网络、界面 | 2026-10-07 GA，Rust / .NET / Node SDK |
| E2B | Firecracker | 配置化权限 | 云端托管，主仓库 Apache-2.0 |
| Daytona | Sysbox 容器命名空间 | 配置化权限 | 生产代码 2026-06-11 起闭源；公开仓库归档于 v0.190.0（2026-06-23） |
| Cloudflare Sandbox SDK | 边缘容器 | 超时、休眠等 | 中文横评记为 Beta，以官方文档为准 |

MXC 已接入的名单以微软原文为准：GitHub Copilot、OpenClaw、OpenAI Codex、Replit、LM Studio、Unsloth AI。NVIDIA OpenShell 补文件、推理服务、凭证和 OCSF 审计。Claude Code、Manus、Perplexity 等在「将要支持」名单里，没有日期。GitHub Copilot 实际用的稳定后端是 Windows ProcessContainer、macOS Seatbelt、Linux bubblewrap。内置文件工具在 harness 里检查，不是子进程级 OS 隔离。Entra 区分 agent 与人、Agent 365 管本机容器，官方写法是即将推出。已经 GA 的是容器执行和 Windows 365 上的 MXC。微 VM 与 Hyperlight 按实验后端对待。

Strands Box 用 `box.toml` 写 Seatbelt 直接授权，用 `policy.dw` 写 Dogwood。解释器、MCP broker 和出口网关跑在沙箱外，共享事件历史，并在网关替换凭证占位符。`box.toml` 直接授权的文件访问不会自动变成 Dogwood 事件。同一 box 里声明的凭证绑定，对该 box 的 agent、工具和 MCP server 都可用。云上多租户要再套每会话微虚拟机；单进程多租户和侧信道在安全说明里明确出界。

冷启动区间（Firecracker 约 90–150 毫秒、Hyperlight 约 0.9 毫秒、第三方把 E2B 写成 150–200 毫秒）不是同一基准，本仓库未复现。Daytona 归档 README 写过专用内核，架构评审写的是 Sysbox；以隔离实现为准。

选型：Apple silicon 上试条件策略用 Box；同一份声明要跨 Windows / macOS / Linux 用 MXC；云上多租户不可信代码用 Firecracker，需要 Dogwood 时把 Box 放进每会话微 VM。

## ACK Agent Sandbox 容器版

这是阿里云产品，不是 `kubernetes-sigs/agent-sandbox`。`ack-sandbox-manager` 0.6.8 起安装 `agents.kruise.io` 的 `TrafficPolicy` / `GlobalTrafficPolicy`，并保留 `network.alibabacloud.com` 一组。`agents.kruise.io` 的 `action` 只有 `allow` 和 `reject`。

**身份。** [`ack-agent-identity`](https://help.aliyun.com/zh/ack/product-overview/ack-agent-identity) 签发身份。`CredentialProvider` 从 Kubernetes Secret、KMS 或 RRSA 取 API Key / 短时 STS。谁能取哪一份由 `AgentRole` / `AgentRoleBinding` 决定。出口网关按 `SecurityProfile.tokenTransformation` 替换占位符或重签名。会话 policy 必须是 RAM 角色权限的子集。存储建议是两层交集：控制面持有最大权限，`CredentialProvider` 再收缩到 subpath；`ListObjects` 要带 `oss:Prefix`。用户委托有两种：UserFederation（授权码 + PKCE）和 DeviceCode（RFC 8628）。刷新令牌和设备码留在服务端，沙箱只拿短时访问令牌。组件版本线看到 0.5.1（2026-09-07）；RRSA 路径要求 0.4.0+，集群 1.28+。

**网络。** `network-policy-mode` 三档：`network-policy`、`traffic-policy`（Poseidon，L4）、`enhanced-traffic-policy`（注入 `traffic-proxy`，L4 目前只管控 TCP，L7 走 `SecurityProfile`，含 MCP `tools/call`）。HTTPS 深度检查要 TLS 终结，并给沙箱注入网关 CA。高权限容器可以绕过命名空间 ACL，所以还要独立安全组。伪造 Host 要靠 L7 域名规则。入站用沙箱维度 JWT，替代 E2B 静态 Token。产品清单里还包括默认拒绝内网、禁止访问 `100.100.100.200`、去掉 `RAW_NET`。

**漂移。** [`ack-agent-sec-scanner`](https://help.aliyun.com/zh/cs/ack-agent-sec-scanner) 在接入前扫 Skill / MCP 制品，接入后按产品最佳实践巡检 `Sandbox`、`SecurityProfile`、`TrafficPolicy`、`CredentialProvider` 等。分类对齐 OWASP Top 10 for Agentic Applications 2026。产品文写明 ASI07、ASI08、ASI10 没有静态规则，留给护栏和 eBPF。

**运行时。** 云安全中心看资产和护栏；Agent 审计按 Trace 和工具调用记录；`SecurityProfile` webhook 把出站命中送到外部系统。Tetragon 以 Sidecar 进沙箱，在 Guest 内核采集进程、文件、网络和 `setuid` / `ptrace`。eBPF 目前要特权，产品文把它放在不共享 PID 命名空间的独立容器里。护栏不能当成 100% 拦截。

## 和开源数据面的对应

| 问题 | ACK 容器版 | OpenKruise Agents |
| --- | --- | --- |
| 长期 AK 不进沙箱 | `CredentialProvider` + RRSA/STS | `tokenTransformation`，Secret 在代理侧解析 |
| 出站与 MCP 工具 | `enhanced-traffic-policy`，双 API Group | `TrafficPolicy` / `SecurityProfile` / `traffic-proxy` |
| 入站动态令牌 | 沙箱 JWT | traffic access token |
| 配置漂移 | `ack-agent-sec-scanner` | 无同名巡检器 |
| 用户委托 | UserFederation / DeviceCode | 路线图提到 Keycloak，尚未等于这套 OAuth |
| 内核证据 | 特权 Tetragon Sidecar | 不是核心组件 |

本机用 MXC 或 Box。集群生命周期用 SIG `agent-sandbox` 或 OpenKruise Agents，隔离另选 RuntimeClass。要云身份、巡检和护栏时再看 ACK 容器版。网关策略不能代替 gVisor 或 Kata。
