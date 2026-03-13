# Agones：Kubernetes 原生的游戏服务器托管平台

> Agones 将专用游戏服务器托管带入 Kubernetes，通过云原生的可扩展性和管理能力
> 支撑多人游戏基础设施。本文探讨正在申请加入 CNCF Sandbox 的 Agones 项目。

## 简介

随着游戏行业的快速发展，对可扩展、可靠的专用游戏服务器基础设施的需求变得至关重要。
Agones 是一个基于 Kubernetes 构建的开源平台，通过提供专门用于托管、运行和扩展
专用游戏服务器的解决方案来满足这一需求。

Agones 源自希腊语 "agōn"，意为"竞赛"或"游戏中的竞争"，它将 Kubernetes 转变为
强大的游戏服务器工作负载管理平台，使用与传统应用相同的云原生原则。

**项目状态：** Agones 已申请加入 CNCF Sandbox
(github.com/cncf/sandbox/issues/440)，
标志着将游戏工作负载引入云原生生态系统的重要一步。

## 什么是 Agones？

Agones 是一个用于在 Kubernetes 上托管、运行和扩展专用游戏服务器的库。它用
Kubernetes 原生 API 和控制器替代了定制或专有的集群管理解决方案。

**核心概念：** 专用游戏服务器是有状态的、临时性的工作负载，与典型的 Web
应用程序有显著不同。每个游戏会话都需要自己的隔离服务器进程，必须保持一致的网络
身份，并且需要专门的生命周期管理。Agones 通过自定义资源定义（CRD）和控制器扩展
Kubernetes 来处理这些独特需求。

### 主要特性

- **GameServer CRD：** 使用 YAML 或 Kubernetes API 声明式地定义单个游戏服务器，
  包含健康检查和连接信息
- **Fleet 管理：** 将大量游戏服务器作为 Fleet 进行管理，类似于 Kubernetes
  Deployment，但针对游戏服务器工作负载进行了优化
- **自动扩缩容：** 与 Kubernetes 集群自动扩缩容原生集成，允许 Fleet
  根据游戏服务器需求进行扩展
- **客户端 SDK：** 提供多种语言的 SDK（Go、C#、C++、Rust、Node.js、REST），
  使游戏服务器能够与 Agones 控制平面通信
- **生命周期管理：** 自动健康检查、优雅关闭处理以及游戏服务器进程的状态管理
- **指标和可观测性：** 游戏服务器专用的指标导出和运维团队仪表板

## 架构与设计

Agones 通过专为游戏服务器工作负载设计的自定义控制器和资源扩展 Kubernetes：

### 自定义资源

- **GameServer：** 代表单个专用游戏服务器实例，包含健康状态、网络端口和连接信息
- **Fleet：** 管理 GameServer 组，提供副本管理、滚动更新和扩缩容能力
- **FleetAutoscaler：** 基于缓冲策略、Webhook 策略或计数器/列表策略自动化
  Fleet 扩缩容
- **GameServerAllocation：** 使匹配系统能够原子性地从 Fleet 中分配 Ready
  状态的 GameServer 供玩家连接

### 工作原理

1. **部署：** 运维人员使用 Kubernetes 清单定义 GameServer 或 Fleet
2. **生命周期管理：** Agones 控制器根据游戏服务器状态创建 Pod 并管理其生命周期
3. **就绪状态：** 游戏服务器使用 Agones SDK 在接受连接时将自己标记为 Ready
4. **分配：** 匹配系统通过 Kubernetes API 请求 GameServer 分配
5. **会话管理：** 游戏服务器在会话结束时通知 Agones，触发清理
6. **自动扩缩容：** FleetAutoscaler 监控 Fleet 状态并调整副本以保持所需的
   缓冲区或响应自定义策略

## 使用场景与生产采用

Agones 专为需要专用游戏服务器的多人游戏场景设计：

- **基于会话的多人游戏：** FPS、MOBA、大逃杀游戏，其中每场比赛都在专用服务器上
  运行
- **持久游戏世界：** MMO 游戏区域或分片，需要长期运行的服务器进程
- **基于比赛的电子竞技：** 需要一致服务器性能的竞技游戏基础设施
- **跨平台游戏：** 用于主机、PC 和移动多人游戏体验的统一基础设施

该项目已被主要游戏公司用于生产环境，并已在规模化场景中证明了其可靠性。CNCF
Sandbox 申请中提到"该项目已被许多组织用于生产环境"。

## 为什么选择 CNCF？

根据 CNCF Sandbox 申请：

> 由于 Agones 与 Kubernetes 紧密耦合，CNCF 是该项目的合理归属。Agones 加入
> CNCF 将带来更广泛的社区贡献者生态系统。

Agones 为 CNCF 生态带来了新的游戏产品，代表了 Kubernetes 的一个特定但重要的
使用场景。随着云原生技术扩展到专业领域，游戏基础设施代表了一个具有独特需求的
重要工作负载类别。

### 云原生集成

Agones 直接与核心 CNCF 项目集成：

- **Kubernetes：** 作为 Kubernetes 控制器与 CRD 构建
- **Prometheus：** 导出指标以监控游戏服务器健康状况和性能
- **Helm：** 通过 Helm chart 进行安装和配置
- **容器运行时：** 适用于任何与 Kubernetes 兼容的容器运行时

## 项目治理与社区

Agones 作为供应商中立的开源项目运营：

- **许可证：** Apache 2.0
- **行为准则：** Contributor Covenant
- **治理：** 清晰的贡献指南和所有权模型
- **社区渠道：** 活跃的 Slack 工作区、邮件列表、定期社区会议
- **维护者：** 最初由 Google Cloud 创建，现在由多个维护者驱动的社区维护

该项目拥有全面的文档、快速入门指南以及面向开发者的示例实现，帮助用户开始在
Kubernetes 上托管游戏服务器。

## 相似项目与生态系统

在 Kubernetes 游戏生态系统中，OpenKruise 的 kruise-game
(github.com/openkruise/kruise-game) 提供了类似的功能。这两个项目都表明了
Kubernetes 上游戏工作负载的兴趣日益增长。

Agones 申请加入 CNCF Sandbox 代表了一个在云原生社区中建立游戏服务器编排标准和
最佳实践的机会。

## 愿景与路线图

Agones 持续进行积极开发，遵循文档化的发布流程定期发布。项目路线图专注于：

- 通过更复杂的策略增强自动扩缩容能力
- 改进游戏服务器运维的可观测性和调试工具
- 扩展对更多编程语言和引擎的 SDK 支持
- 大规模部署的性能优化
- 与匹配系统和大厅系统的更好集成

该项目旨在使专用游戏服务器托管像部署无状态 Web 应用一样简单可靠，同时尊重实时
游戏工作负载的独特要求。

## 开始使用

对于有兴趣探索 Agones 的开发者：

1. **文档：** agones.dev/site/docs/ 上的综合指南
2. **快速入门：** 在 Kubernetes 集群上安装 Agones 并部署一个简单的游戏服务器
3. **示例：** 仓库中有多个游戏服务器实现示例
4. **社区：** 加入 Agones Slack 和邮件列表以获取支持和讨论

Agones 代表了游戏基础设施向云原生时代的成熟，将 Kubernetes 的运维优势带给最
苛刻的实时工作负载类型之一。

## 总结

Agones 将 Kubernetes 转变为强大的专用游戏服务器托管平台，解决了多人游戏基础
设施的独特挑战。随着它申请加入 CNCF Sandbox，该项目展示了云原生技术如何在保持
Kubernetes 原生原则的同时适应专业化的工作负载需求。

对于构建多人游戏体验的游戏公司和管理游戏服务器的基础设施团队，Agones 提供了
一个经过验证的、生产就绪的解决方案，充分利用了云原生工具和实践的完整生态系统。

---

**参考资料：**

- Agones GitHub：github.com/googleforgames/agones
- 官方网站：agones.dev/site/
- CNCF Sandbox 申请：github.com/cncf/sandbox/issues/440
- 公告博客：cloud.google.com/blog/products/containers-kubernetes/
  introducing-agones-open-source-multiplayer-dedicated-game-server-hosting-
  built-on-kubernetes
