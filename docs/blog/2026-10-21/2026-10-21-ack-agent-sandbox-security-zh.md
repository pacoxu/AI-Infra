---
status: Active
maintainer: pacoxu
date: 2026-10-21
last_updated: 2026-10-21
tags: agent-sandbox, aliyun, ack, credential-provider, traffic-policy, tetragon, ai-infrastructure
canonical_path: docs/blog/2026-10-21/2026-10-21-ack-agent-sandbox-security-zh.md
source_urls:
  - https://help.aliyun.com/zh/ack/product-overview/ack-agent-identity
  - https://help.aliyun.com/zh/agent-sandbox/user-guide/use-kubernetes-secret-api-key-credentials-with-credentialprovider
  - https://help.aliyun.com/zh/agent-sandbox/user-guide/use-the-credentials-provider-to-configure-the-temporary-credentials-of-the-ram-role-sts
  - https://help.aliyun.com/zh/agent-sandbox/user-guide/manage-agent-sandbox-egress-traffic
  - https://help.aliyun.com/zh/cs/ack-agent-sec-scanner
  - https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/
  - https://github.com/openkruise/agents
---

# 不止于沙箱：ACK Agent Sandbox 容器版的安全面

阿里云 Agent Sandbox 容器版把企业 Agent 的安全写成三层：身份与凭据、基线、运行时。模型拒绝恶意提示只覆盖其中一层。沙箱里的代码可能是模型现写的，也可能已经被提示注入改过，所以上线前的镜像扫描盖不住「执行时还不存在的代码」。

它和本仓库里另外两篇不是同一层：

- [OpenKruise Agents v0.6.0](./2026-10-21-openkruise-agents-v0.6.0_zh.md) 是开源数据面。ACK 从 `ack-sandbox-manager` 0.6.8 起会装 `agents.kruise.io` 的 `TrafficPolicy` / `GlobalTrafficPolicy`，并同时保留 `network.alibabacloud.com` 这一组。增强流量策略把两边都接上。
- [MXC 与 Strands Box](./2026-10-21-mxc-strands-box-sandbox-review_zh.md) 是本机策略沙箱。这里是托管 Kubernetes 上的身份、网络、巡检和运行时检测。

生产检验仍然简单：打开 Sandbox，里面不该有长期 AK。有的话，安全性就押在模型不把密钥打进日志、不把密钥外发。模型会犯错。

## 身份与凭据

[`ack-agent-identity`](https://help.aliyun.com/zh/ack/product-overview/ack-agent-identity)
负责签发身份和管理出口凭据。帮助中心记到的版本线：0.2.0-beta.5（2026-06-10）起步，0.4.0（2026-07-22）加上 OSS 动态挂载所需的 STS 和 OAuth2，0.4.1 加上 E2B 链路的 Traffic Access Token，0.5.0 支持跨账号 STS 和 KMS 凭据管家，0.5.1（2026-09-07）加上 AgenticBucket / AgenticFS 的策略模板函数、自建凭据服务和 JWT 类型的 `CredentialProvider`。集群版本要求 1.28+；RRSA 路径要求组件 0.4.0+。

`CredentialProvider`（`agentidentity.alibabacloud.com/v1alpha1`）是凭据来源。谁能取哪一份，由 `AgentRole` / `AgentRoleBinding` 决定。

| 类型 | 来源 | 沙箱里看到的 |
| --- | --- | --- |
| `APIKey` | Kubernetes Secret、KMS 凭据管家 | 占位请求。出口网关按 `SecurityProfile.tokenTransformation` 换成真实 Key |
| `RAM` | RRSA，`AssumeRoleWithOIDC` | 短时 STS（`AccessKeyId` / `AccessKeySecret` / `SecurityToken`）。会话 `policy` 必须是角色权限的子集，可用模板变量按身份和实例收缩 |

`secretRef.name` 可以带模板变量，同一份配置按身份取不同 Secret。云 API 的重签名发生在出口网关，业务容器不持有用来签名的长期密钥。

存储权限在产品文里被写成两层交集。第一层用 RRSA 把存储所需的最大权限交给 `ack-agent-identity`，边界留在控制面。第二层由权限管理员在 `CredentialProvider` 里声明租户的最小权限。下发的 STS 是这两层的交集，再落到 subpath。模板函数配合 `SandboxClaim` 带进来的业务参数，避免为每个前缀手写一份策略。官方 STS 文档里的对应约束是：`ListObjects` 要加 `oss:Prefix` 条件，`tokenValidity` 示例为 3600 秒。

产品文给出的存储清单，当作建议而不是本仓库实测：

- 租户数据用 subPath，各自一个 `CredentialProvider`
- 认证走 Agent Identity（RRSA + STS），沙箱不留长期凭据
- `ListObjects` 带 `oss:Prefix`
- OSS 走 HTTPS 内网 Endpoint，签名用 SigV4
- 共享存储默认 `readOnly: true`

### 用户委托：OAuth 三方

Agent 代表用户打开文档或代码仓库时，要证明的是谁让它来、它是谁、这扇门是否还开着。`ack-agent-identity` 提供两种委托，应用密钥、刷新令牌和 Device Code 的轮询码留在可信服务端，沙箱按需拿短时访问令牌：

- **UserFederation**：授权码 + PKCE，给 Web、控制台和 IDE。授权页展示请求方 Agent 和权限范围。
- **DeviceCode**：RFC 8628。沙箱里没有浏览器、也不暴露 OAuth 回调；用户在自己的电脑或手机上打开验证链接。省掉的是沙箱里的浏览器，不是用户同意。

授权会话由平台保存，并在仍然有效且对方支持刷新时自动续期。

## 基线：网络、入站令牌、配置漂移

沙箱在这套方案里被标成不可信算力。多租户要拆独立 vSwitch 和企业安全组，这是网络兜底，不是可选项。

`network.alibabacloud.com/network-policy-mode` 有三档：

| 模式 | 做什么 | 依赖 |
| --- | --- | --- |
| `network-policy` | 只用 Kubernetes NetworkPolicy | 集群网络策略 |
| `traffic-policy` | `TrafficPolicy` 的 L4 入站和出站 | Poseidon |
| `enhanced-traffic-policy` | 注入 `traffic-proxy`。L4 走 `TrafficPolicy`（当前只管控 TCP），L7 走出站 `SecurityProfile` | `ack-sandbox-manager` 打开增强流量管理 |

L7 能按域名、路径、方法、头和查询参数匹配，也能按 JSON-RPC `tools/call` 的 `params.name` 做 MCP 工具 ACL。HTTPS 要做 TLS 终结才进得了 L7；产品文写的做法是注入网关 CA，并设置 `SSL_CERT_FILE`、`NODE_EXTRA_CA_CERTS`，让沙箱里的常规 HTTPS 客户端不用改代码。`SecurityProfile` 还可以把声明过的出站地址和头绑到指定的 Agent Identity / `CredentialProvider`，以及用 webhook 把命中事件送出去。

官方限制要和策略一起读：

- `NET_ADMIN`、`SYS_ADMIN`、`CAP_SETUID`、`CAP_SETGID`、`privileged` 或 root 可以绕过网络命名空间里的 ACL。所以要有独立安全组，再用 `GlobalTrafficPolicy` 的入站规则和安全组入方向，挡住沙箱访问非沙箱工作负载。
- 网关按 Host 选上游，连上的地址可以和 `TrafficPolicy` 校验过的原始目的地不同。伪造 Host 时要靠 `SecurityProfile` 的域名规则补一层。
- `agents.kruise.io` 的 `TrafficPolicy` 里 `action` 只有 `allow` 和 `reject`，其余与 `network.alibabacloud.com` 那一组对齐。

入站侧，社区 E2B 的静态 Token 被换成沙箱维度的 JWT。客户端取令牌，网关统一验。这对应 `ack-agent-identity` 0.4.1 的 Traffic Access Token。控制面和数据面流量要分开。

产品文的网络清单：打开 `enhanced-traffic-policy`；默认拒绝内网，防横向移动；独立企业安全组、组内隔离和端口矩阵；公网用 `SecurityProfile` 白名单；`GlobalTrafficPolicy` 禁止访问 `100.100.100.200`（阿里云元数据）；入站用 JWT；沙箱去掉 `RAW_NET`，避免嗅探和劫持。

### ack-agent-sec-scanner

基线写在文档里，仍会在排障时被改宽：元数据禁令被注释，`CredentialProvider` 的 `Resource` 写成 `*`。沙箱不会因此起不来。

[ack-agent-sec-scanner](https://help.aliyun.com/zh/cs/ack-agent-sec-scanner) 做两件事。接入前，对上传的 Skill 和 MCP Server 做静态分析：恶意代码、危险命令、凭据泄露、提示词注入、过度授权。接入后，周期读取 `Sandbox`、`SandboxSet`、`SecurityProfile`、`TrafficPolicy`、`CredentialProvider`、`AgentRole`、`PersistentVolume` 等，按产品自己的安全最佳实践做断言。另有一项默认关闭的 AI 基础设施端点探测，对照 CVE。接口是控制台、可放进 CI 和准入的 API、报告导出。

扫描分类对齐 [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/)（2025 年 12 月发布的 ASI）。例如 ASI05 是 Unexpected Code Execution。产品文写明 ASI07、ASI08、ASI10（Agent 间通信、级联失效、Rogue Agents）没有静态规则，留给护栏和 eBPF。这是覆盖边界，不是扫描器已经处理了运行时。

## 运行时：护栏、审计、内核事件

凭据不进沙箱，只说明密钥不在环境变量里。被诱导的 Agent 仍可以走合法通道：读工单里的间接指令、加载带隐藏提示的 Skill、调用本来就有的工具。这些调用在系统调用上看起来和正常任务一样。所以运行时要另三层，而且都不能单独覆盖全部风险。

**资产。** 云安全中心把模型服务、推理引擎、工作流、向量库和工具收进一个视图，看漏洞、配置、公网暴露和明文密钥。Serverless 沙箱要可见，产品文的接法是在模板上声明 `security.alibabacloud.com/aliyundun-enabled: "true"`，并开通对应检测。这是云产品开关，不是开源 CRD。

**护栏。** Agent 安全中心覆盖提示词攻击、越狱、内容合规、敏感数据外泄、行为偏离、目标劫持和资源滥用。产品文给出的 RASP 接入是：集群装 `ack-onepilot`，沙箱模板加 `raspPilotAutoEnable`、`raspPilotAmsKey`、`raspPilotLang`、`raspPilotRegion`，再滚动 `SandboxSet`。拦截例子是字符混淆后的恶意链接。护栏评测不能当成 100% 拦截，尤其是长链和组合攻击；产品文自己也这样写。

**审计与内核。** Agent 审计日志按 Agent、Trace、模型和工具调用看统计。自定义审计可以用 `SecurityProfile` 的 webhook，把匹配到的出站请求送到已有系统。进程、文件和网络要看执行侧时，产品实践是把 Cilium Tetragon 以 Sidecar 放进沙箱，在 Guest 内核加载 eBPF，用 `TracingPolicy` 描述探测点。典型面是进程起停和父子关系、敏感路径写入和删除、TCP 连接元数据，以及 `setuid`、`ptrace` 一类调用。Prometheus 端口可以对 ARMS 自动发现，JSON 事件可以进 SLS。

eBPF 目前要特权。产品文把这个特权放在单独的、功能单一的容器里，并且不和业务容器共享 PID 命名空间。观测边界因此和沙箱边界对齐，但特权容器本身仍是攻击面，不能为了采集去放宽业务容器。

护栏回答「这次交互像不像攻击」，审计回答「调用了哪个工具」，Tetragon 回答「这个工具又起了什么进程、碰了什么文件和连接」。三份记录要能对上同一次任务，才谈得上处置。

## 和开源数据面怎么摆

| 问题 | ACK 容器版 | 开源对应 |
| --- | --- | --- |
| 长期 AK 不进沙箱 | `CredentialProvider` + 出口注入 + RRSA/STS | OpenKruise `tokenTransformation`，Secret 在代理侧解析 |
| 出站白名单和 MCP 工具 | `enhanced-traffic-policy`，双 API Group | `TrafficPolicy` / `SecurityProfile` / `traffic-proxy` |
| 入站不是静态 Token | 沙箱维度 JWT | traffic access token |
| 基线会漂 | `ack-agent-sec-scanner` | 开源侧没有同名巡检器 |
| 用户委托 | UserFederation / DeviceCode | 路线图里的 Keycloak 一类身份对接尚未等于这套 OAuth |
| 内核证据 | Tetragon Sidecar，特权、不共享 PID | 不是 Agents 核心组件 |

身份回答代表谁，基线回答能碰什么，运行时回答实际发生了什么。三层同时在，才是这套产品文里的「纵深」。只开沙箱、把 AK 放进环境变量，不在这套体系里。

---

*整理自阿里云帮助中心（ack-agent-identity、CredentialProvider、增强出口流量、ack-agent-sec-scanner）和 Agent Sandbox 容器版安全产品文。控制台截图未转写。RASP 标签、Tetragon 部署形态和存储/网络清单以产品文为准，落地前对照当前帮助中心。*
