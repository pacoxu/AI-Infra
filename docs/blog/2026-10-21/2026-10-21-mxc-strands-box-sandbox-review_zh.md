---
status: Active
maintainer: pacoxu
date: 2026-10-21
last_updated: 2026-10-21
tags: agent-sandbox, mxc, strands-box, e2b, daytona, dogwood, ai-infrastructure
canonical_path: docs/blog/2026-10-21/2026-10-21-mxc-strands-box-sandbox-review_zh.md
source_urls:
  - https://blogs.windows.com/windowsdeveloper/2026/10/07/microsoft-execution-containers-policy-driven-containment-for-ai-agents/
  - https://github.com/microsoft/mxc
  - https://github.blog/changelog/2026-10-07-local-sandboxing-for-github-copilot-now-generally-available/
  - https://aws.amazon.com/blogs/opensource/introducing-strands-box-ai-agent-sandboxes-powered-by-dogwood/
  - https://strandsagents.com/blog/strands-box-the-big-picture/
  - https://github.com/strands-agents/box
  - https://strandsagents.com/docs/user-guide/box/
  - https://www.daytona.io/dotfiles/updates/daytona-is-going-closed-source
  - https://github.com/daytonaio/daytona
  - https://github.com/e2b-dev/e2b
---

# 智能体沙箱换代：MXC 与 Strands Box 同日发布

2026-10-07，微软和 AWS 隔了几个小时，为同一件事各发了一份公告：智能体拿到文件系统、网络和工具调用之后，怎样保证它只做被授权的事。两边的重点都从「能不能碰到这个资源」走到「在什么条件下才允许这一次动作」。策略放在工作负载外面，被管住的 agent 不能给自己扩权。

这一天同时站住的还有云上托管沙箱。本地还是云端、进程级还是虚拟机级、带不带语义策略引擎，是现在选型的三条分界。Kubernetes 上的生命周期和数据面是第四条，见同日整理的
[OpenKruise Agents v0.6.0](./2026-10-21-openkruise-agents-v0.6.0_zh.md)。

## 同一天的两份公告

[Microsoft Execution Containers（MXC）](https://blogs.windows.com/windowsdeveloper/2026/10/07/microsoft-execution-containers-policy-driven-containment-for-ai-agents/)
结束自 Build 2026 起的预览，当天 GA。代码在
[microsoft/mxc](https://github.com/microsoft/mxc)。SDK v1.0.0 覆盖 Rust、.NET、Node；
10 月 17 日的 v1.0.1 是补丁，稳定 schema 仍是 `1.0.0`。开发者用一份 JSON 声明
文件路径、网络目的地和界面权限，运行时再映射到所选后端。同一份声明可以落在
本地设备，也可以落到已经 GA 的 Windows 365。

仓库列出的后端包括 ProcessContainer、Windows Sandbox、LXC、Bubblewrap、Seatbelt、
MicroVM（Nanvix）、Hyperlight、IsolationSession、WSLC。GitHub Copilot 的本地沙箱
已经用上其中三条稳定路径：Windows 上是 ProcessContainer 的 BaseContainer，macOS
上是 Seatbelt，Linux 上是 bubblewrap。这些路径不要求单独的虚拟机或容器镜像。
微 VM 与 Hyperlight 仍应按仓库里的实验标注对待，不要写成 GA 的默认隔离。

微软点名已经接入的有 GitHub Copilot、OpenClaw、OpenAI Codex、Replit、LM Studio、
Unsloth AI。NVIDIA 把 OpenShell 接进 MXC，补文件与推理服务的访问策略、网络控制、
凭证管理和面向企业的 OCSF 审计。微软还列出将要支持、但没有给日期的名单：Claude
Code、Box、Egnyte、Heidi Health、Hermes Agent、Manus、Perplexity、Raycast、
Simular 等。这是微软对其他产品的陈述，第二组还不能算已经交付。

身份和管控要比容器本身晚一步。官方写法是 Windows **即将**用 Entra 把 agent 行为
和人类账户分开，并把 Agent 365 的管控延伸到本机上的 MXC。已经 GA 的是容器执行
和 Windows 365 上的 MXC，不是一整条 Intune / Entra 闭环。

[Strands Box](https://aws.amazon.com/blogs/opensource/introducing-strands-box-ai-agent-sandboxes-powered-by-dogwood/)
同一天以 developer preview 开源，协议 Apache-2.0，仓库
[strands-agents/box](https://github.com/strands-agents/box)，版本 v0.1.0。它不绑
模型，也不绑 Strands harness。当前只支持 macOS 15+ 的 Apple silicon。配置拆成
两份：`box.toml` 写操作系统直接授权，`policy.dw` 用 Dogwood 写条件策略。Dogwood
兼容 Cedar，并带时间算子。

## 策略可以写在哪一层

[Marc Brooker 的配套文](https://strandsagents.com/blog/strands-box-the-big-picture/)
把取舍写成三层。层越高，策略越能读懂动作；受信计算基也越大。

**设备级。** Firecracker 微虚拟机是 Lambda 和 AgentCore Runtime 的选择。guest
和宿主机之间只剩少量模拟设备上的字节：TLS 密文、块设备读写。安全姿态好，受信
计算基小。能强制「流量必须走这个网关」，很难从密文里读出「这次是不是支付、金额
有没有超限」。

**系统调用级。** 容器和 gVisor 看得见 `open`、`listen`、`connect`，可以写路径和
主机。syscall 表还在变，名单要一直补。网络上仍是密文。MCP 工具名、git 子命令
这类语义不在 syscall 的词汇里。

**语义级。** Strands Box 仍用内核隔离把门，但把需要裁决的动作收进少数出口：
Strands Shell、Python 的 Monty、MCP broker、出口网关。这些解释器和网关跑在 Box
自己的进程里，位于沙箱之外；agent 把它们当成本机的 `bash`、`python3` 和 MCP。
出口共享一份事件历史，所以可以写「读过某文件之后禁止外发」，也可以写时间窗口
和次数上限。默认拒绝：没有匹配的 `permit` 就拒绝，匹配的 `forbid` 覆盖
`permit`。出口网关终结 TLS，把凭证占位符换成真实值。

`box.toml` 里授权的直接文件和程序访问由 macOS Seatbelt 执行。Dogwood 管的是经过
上述出口的动作。直接按授权打开的文件，不会自动变成策略事件。同一个 `box.toml`
声明的凭证绑定，对该 box 里的 agent、工具和 MCP server 都可用；不该拿到凭证的
进程要放到另一个 box。安全说明还把「单进程里的多租户隔离」和侧信道划在边界外：
一个 box 只关一个工作负载。

代价写在官方文里。解释器和协议拦截器都在受信计算基里，代码更多，bug 就可能变成
策略绕过。实现是 Rust，并做了测试、模糊测试和校验。云上多租户的建议是再套一层
每会话微虚拟机：最省事的是把 Box 跑在 AgentCore Runtime 里，同样的结构也可以放在
EC2、Lambda 或 Fargate 上。那样同时有 Box 的本地细策略、AgentCore Policy 的工具
策略，以及会话之间的微虚拟机边界。

## 五款对照

状态按 2026 年 10 月中旬的官方材料。冷启动不放进这张表：各家数字不是同一基准。

| 产品 | 隔离 | 策略 | 位置与状态 |
| --- | --- | --- | --- |
| [Strands Box](https://github.com/strands-agents/box) | macOS Seatbelt | Dogwood：默认拒绝，可写时序和跨出口规则 | 本地预览，Apache-2.0，仅 Apple silicon / macOS 15+ |
| [MXC](https://github.com/microsoft/mxc) | 进程、会话、WSL、实验性微 VM 等多后端 | 一份 JSON：文件、网络、界面 | 本地与 Windows 365，2026-10-07 GA，开源 SDK |
| [E2B](https://github.com/e2b-dev/e2b) | Firecracker 微 VM | 配置化权限 | 云端托管，主仓库 Apache-2.0 |
| [Daytona](https://github.com/daytonaio/daytona) | 容器命名空间（Sysbox） | 配置化权限 | 生产代码 2026-06-11 起闭源；公开仓库归档，最后开源版本 v0.190.0（2026-06-23） |
| Cloudflare Sandbox SDK | 边缘容器，共享内核 | 超时、休眠等运行配置 | 云端边缘，中文横评记为 Beta，以 Cloudflare 文档为准 |

Daytona 需要单独看隔离口径。归档仓库的 README 写过专用内核和 90 毫秒内启动；
项目自己的架构评审则写明是 Sysbox 容器命名空间，不是 hypervisor。营销句和实现
说明不一致时，以隔离实现为准。公开仓库不再维护，SDK 和文档改到
[github.com/daytona](https://github.com/daytona)。

冷启动只保留横评里已经写明、且标明不是同条件实测的区间：Firecracker 一类大约
90–150 毫秒，Hyperlight 这类无客户机内核路径大约 0.9 毫秒，第三方对比把 E2B
冷启动写成约 150–200 毫秒。本仓库没有复现。E2B「暂停 30 天后删除、单次会话
1–24 小时」来自第三方对比，不当成当前配额。

Copilot 还有一条和「所有出口都由操作系统强制」不完全重合的实现：内置文件工具
在 harness 里对照策略检查，不是子进程级的 OS 隔离；远程 MCP 也不在本地进程沙箱
里。本地 MCP 和 language server 在支持的情况下才会进进程边界。

## 两条路线，加上集群上的第三条

MXC 和 Box 暂时不是互相替换。

MXC 的强项是平台纵深：一份 JSON 映射到 Windows、macOS、Linux 的不同后端，三套
SDK，Windows 365 已经能跑。策略粒度停在文件、网络、界面。用活动记录反推最小权限
的能力，社区对 1.0 的阅读是目前更依赖 Windows。

Box 的强项是单点表达力：动作、参数、顺序和时间可以写进同一份 Dogwood 策略。
代价是策略引擎本身在受信名单里，而且今天只能在 Apple silicon 的 Mac 上预览。

集群侧已经有对应物，只是 API 不同。OpenKruise Agents v0.6.0 把 L4 拒绝、L7 /
MCP 工具 ACL 和 Secret 凭证注入放在 Pod 内代理和出口网关上，解决的是 Kubernetes
里一批 Sandbox 的流量和生命周期，不是开发者笔记本上的 Seatbelt。SIG
`agent-sandbox` 则提供中立的认领和预热池 CRD，隔离仍要另选 RuntimeClass。

## 选型

1. **本机、要条件化边界，而且机器是 Apple silicon：** 用 Strands Box 看动作级策略。策略语言和键还在 0.1.x，升级要钉住版本。
2. **同一份声明要跨 Windows、macOS、Linux，或要进 Windows 365：** 用 MXC SDK。默认后端按 Copilot 已采用的进程沙箱理解；微 VM 单独评估。
3. **云上多租户跑不可信代码：** Firecracker 托管（E2B，或自管微 VM）承担隔离。若还要 Dogwood 那种条件，按 AWS 的建议把 Box 放进每会话微 VM，不要在一个 OS 进程里混租户。
4. **已经在 Windows 企业环境里：** MXC 加 Windows 365 是现在能落地的链路。Entra 区分 agent 与人、Agent 365 管本机容器，按「即将」跟踪，不要写进当前架构的已交付清单。
5. **要看 Daytona：** 生产路径是闭源代码和托管服务；要审计实现，只能看归档的 v0.190.0，且它不再收安全修复。

隔离层级决定安全下限，策略表达力决定能把规则写成多细。两件事仍然要一起选。

---

*整理自微软 Windows 开发者博客、MXC 仓库、GitHub Copilot 更新日志、AWS Open
Source 博客、Strands Box 文档与安全说明、Daytona 闭源说明。客户接入名单以微软
原文为准。冷启动和 E2B 会话保留时间是社区或第三方口径，未在本仓库复现。*
