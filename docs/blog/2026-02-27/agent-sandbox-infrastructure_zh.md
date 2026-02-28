---
status: Active
maintainer: pacoxu
last_updated: 2026-02-27
tags: browser-use, agent-sandbox, unikraft, micro-vm, security, scalability, cloud
canonical_path: docs/blog/2026-02-27/agent-sandbox-infrastructure_zh.md
---

# 我们如何构建安全、可扩展的 Agent 沙箱基础设施

> 原文：
> <a href="https://browser-use.com/posts/two-ways-to-sandbox-agents">How We Built
> Secure, Scalable Agent Sandbox Infrastructure</a>（browser-use 官方博客）

## 背景

<a href="https://browser-use.com">Browser Use</a> 是一个让 AI Agent 能够
自动操作浏览器的开源框架（79k+ GitHub Stars），并提供配套的云服务
<a href="https://cloud.browser-use.com">Browser Use Cloud</a>。
在云服务场景下，用户提交的 Agent 任务会真实地在浏览器中执行——登录网站、
填写表单、抓取数据——这意味着每个 Agent 实例都拥有完整的浏览器能力，
可以访问任意网站、执行任意 JavaScript。

这引出了一个核心安全问题：**如何确保每个 Agent 任务在严格隔离的沙箱中运行，
既防止恶意任务逃逸影响其他用户，也防止 Agent 访问平台基础设施的敏感凭据？**

随着 Cloud 产品从早期测试走向规模化生产，我们先后探索了两种沙箱方案，
最终形成了当前基于 Unikraft 微虚拟机的全栈沙箱化架构。

## 为什么 Agent 沙箱比普通容器更难

传统 Web 服务的隔离相对简单——用 Docker 容器、限制网络出口、
配置资源限额，基本就够了。但 AI Agent 有其特殊性：

- **高权限操作**：Agent 需要完整的浏览器环境（Chromium）、
  能执行任意代码（LLM 生成的脚本）、能访问任意外部网站
- **长时运行**：一个 Agent 任务可能持续数分钟甚至数十分钟，
  期间系统状态随时变化
- **侧信道风险**：共享宿主机内核的容器隔离存在内核漏洞利用的风险，
  对多租户场景尤为敏感
- **凭据保护**：Agent 运行时不应能访问云平台的 IAM 密钥、
  数据库连接串等基础设施凭据

标准 Docker 容器在面对这些需求时显得力不从心，
我们需要更强的隔离边界。

## 第一种方案：AWS Lambda

### 初始选择

最初，我们选择 **AWS Lambda** 作为 Agent 的执行环境。
Lambda 的优势显而易见：

- **零运维**：无需管理服务器，自动伸缩
- **天然隔离**：每次调用都在独立的 MicroVM（AWS Firecracker）中运行，
  彼此完全隔离
- **按需计费**：只为实际运行时间付费，成本可控

每个 Agent 任务触发一次 Lambda 调用，内部启动 Chromium、
运行 browser-use 框架，任务完成后实例销毁。

### Lambda 方案的局限

随着业务增长，Lambda 方案暴露出几个关键问题：

**1. 冷启动延迟**

Chromium 本身体积较大（~300MB），Lambda 的冷启动时间可达
数秒，对用户体验影响明显。虽然可以通过预置并发（Provisioned
Concurrency）缓解，但成本随之上升。

**2. 执行时间限制**

Lambda 最长执行时间为 15 分钟。对于复杂的 Agent 任务，
这个上限有时不够用，且任务被强制中断后很难优雅地恢复状态。

**3. 有限的自定义能力**

Lambda 运行环境相对封闭，难以精细控制网络策略、
文件系统挂载、系统调用过滤等底层配置。
对于需要强安全保证的多租户场景，这种不透明性令人担忧。

**4. 供应商锁定**

整个执行层深度依赖 AWS Lambda 的 API 和计费模型，
迁移成本高，也限制了对执行环境的掌控度。

## 第二种方案：Unikraft 微虚拟机

### 为什么选择 Unikraft

<a href="https://unikraft.org">Unikraft</a> 是一个开源的 Unikernel
构建工具，能够将应用程序打包成极轻量的虚拟机镜像（Unikernel），
直接运行在 KVM 虚拟化层之上，无需完整的操作系统。

相比 Lambda，Unikraft 微虚拟机具备：

- **更快的启动时间**：Unikernel 镜像极小（通常 < 10MB），
  启动时间可低至 **10-50ms**，远优于 Lambda 冷启动
- **更强的安全隔离**：每个 Agent 拥有独立的内核实例，
  完全隔离于宿主机内核，攻击面极小
- **完全可控**：我们自己管理 Hypervisor 层，
  可以精细配置每个 MicroVM 的网络、存储、CPU/内存限额
- **无供应商锁定**：可以在任意支持 KVM 的云主机或裸金属上运行

### 架构设计

新架构的核心是一个**控制平面（Control Plane）**，
负责管理所有 MicroVM 的生命周期：

```text
┌─────────────────────────────────────────────────────────────┐
│                     Browser Use Cloud                        │
│                                                              │
│  ┌──────────────┐    ┌──────────────────────────────────┐   │
│  │  API Gateway │───▶│        Control Plane             │   │
│  │              │    │  - Task 调度                      │   │
│  │  用户请求     │    │  - MicroVM 生命周期管理           │   │
│  └──────────────┘    │  - 健康检查与自动恢复              │   │
│                      │  - 无密钥凭据注入                  │   │
│                      └────────────┬─────────────────────┘   │
│                                   │                          │
│              ┌────────────────────┼───────────────────┐     │
│              ▼                    ▼                    ▼     │
│  ┌──────────────────┐ ┌──────────────────┐ ┌────────────┐  │
│  │  Unikraft MicroVM│ │  Unikraft MicroVM│ │  MicroVM   │  │
│  │  ┌────────────┐  │ │  ┌────────────┐  │ │  (热备池)  │  │
│  │  │ Browser Use│  │ │  │ Browser Use│  │ │            │  │
│  │  │  Agent     │  │ │  │  Agent     │  │ └────────────┘  │
│  │  │ + Chromium │  │ │  │ + Chromium │  │                  │
│  │  └────────────┘  │ │  └────────────┘  │                  │
│  │  隔离网络/存储    │ │  隔离网络/存储    │                  │
│  └──────────────────┘ └──────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### 无密钥安全模型

这是整个架构中最关键的安全设计之一。

**问题**：Agent 在执行某些任务时可能需要访问外部服务（如数据库、
API），但我们绝不能让 Agent 持有任何云平台的 IAM 密钥或
服务账号凭据——一旦 Agent 被恶意指令控制，后果不堪设想。

**解决方案**：采用**无密钥（Keyless）**架构：

1. **MicroVM 与凭据完全隔离**：MicroVM 内部不存储任何长期凭据
2. **控制平面代理所有授权操作**：Agent 需要访问受保护资源时，
   必须通过控制平面的 API 发起请求，由控制平面持有并使用凭据
3. **细粒度权限控制**：每个 Agent 任务只被授权访问其明确需要的
   最小资源集合
4. **审计日志**：所有经过控制平面的授权操作均被记录，
   便于安全审计和异常检测

### 弹性伸缩与热备池

为了解决 MicroVM 启动延迟（即使 Unikraft 很快，
在高并发下也需要提前准备），我们引入了**热备池（Warm Pool）**机制：

- 控制平面持续维护一定数量的空闲 MicroVM
- 新任务到来时，立即从热备池分配，实现**亚秒级响应**
- 任务完成后，MicroVM 被销毁（而非回收复用），
  确保任务间不留任何状态残留
- 控制平面根据当前负载动态调整热备池大小，
  在成本和响应速度之间取得平衡

## 两种方案的对比

| 维度 | AWS Lambda | Unikraft MicroVM |
| --- | --- | --- |
| 冷启动 | 数秒（无预置并发时） | < 50ms |
| 最长执行时间 | 15 分钟 | 无限制 |
| 隔离强度 | 中（共享 AWS 基础设施） | 高（独立内核实例） |
| 网络策略控制 | 有限 | 完全自定义 |
| 成本模型 | 按调用次数+时间 | 按资源使用量 |
| 供应商依赖 | 强（AWS） | 无（可迁移） |
| 运维复杂度 | 低 | 中高 |
| 自定义能力 | 低 | 高 |

对于早期阶段或低并发场景，Lambda 依然是快速验证的好选择；
但当业务规模扩大、安全要求提高、需要精细控制执行环境时，
自建 MicroVM 控制平面是值得投入的方向。

## 经验总结

回顾这段演进历程，有几点体会值得分享：

**1. 越早考虑安全模型越好**

从 Lambda 迁移到 MicroVM 不仅仅是技术替换，
还需要重新设计凭据管理、网络架构、监控体系。
如果能在早期就规划好安全模型，迁移成本会低很多。

**2. 隔离粒度要匹配威胁模型**

并非所有场景都需要 Unikernel 级别的隔离。
普通的 Web 服务用 gVisor 或 Kata Containers 可能就足够了。
Browser Agent 因为其特殊的权限需求，才需要更强的隔离。

**3. 控制平面是关键投资**

强大的控制平面不仅管理 MicroVM 生命周期，
更是安全策略、弹性伸缩、可观测性的核心枢纽。
这部分的投入会在整个系统运行期间持续产生价值。

**4. 开源工具让自建成为可能**

Unikraft、Firecracker（AWS 开源）、
KVM 等开源工具的成熟，让中小型团队也有能力构建媲美大厂的
沙箱基础设施。站在这些开源项目的肩膀上，
我们的团队以相对较小的投入实现了生产级别的安全保障。

## 关联阅读

Browser Use 的沙箱实践代表了 AI Agent 基础设施领域的一个重要趋势：
随着 AI Agent 从实验阶段走向生产，安全隔离从"锦上添花"变成了
"不可或缺"。相关的 Kubernetes 生态进展也值得关注：

- **Agent Sandbox（kubernetes-sigs）**：Kubernetes SIG Apps 旗下的
  Agent 沙箱项目，提供标准化的 Sandbox CRD，支持 gVisor 和
  Kata Containers，并内置 WarmPool 机制——思路与 browser-use 的
  实践高度相似。详见本站
  <a href="../2025-11-28/agent-sandbox.md">Agent Sandbox 介绍</a>。

- **gVisor / Kata Containers**：主流的容器级沙箱技术，
  适合对 Agent 进行轻量级隔离。

- **Unikraft**：用于构建 Unikernel/MicroVM，
  提供更强的隔离与更快的启动速度，
  适合对安全要求更高的多租户 Agent 场景。

## 参考资料

- 原文：
  <a href="https://browser-use.com/posts/two-ways-to-sandbox-agents">
  How We Built Secure, Scalable Agent Sandbox Infrastructure</a>
- Browser Use Cloud：
  <a href="https://cloud.browser-use.com">https://cloud.browser-use.com</a>
- Unikraft 官网：
  <a href="https://unikraft.org">https://unikraft.org</a>
- kubernetes-sigs/agent-sandbox：
  <a href="https://github.com/kubernetes-sigs/agent-sandbox">
  https://github.com/kubernetes-sigs/agent-sandbox</a>
- Kata Containers Agent Sandbox 集成博客：
  <a href="https://katacontainers.io/blog/Kata-Containers-Agent-Sandbox-Integration/">
  https://katacontainers.io/blog/Kata-Containers-Agent-Sandbox-Integration/</a>
