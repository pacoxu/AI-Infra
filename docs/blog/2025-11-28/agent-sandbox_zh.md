# Agent Sandbox：在 Kubernetes 上安全运行 AI 代理

> Agent Sandbox 为 AI 代理提供安全、隔离和高效的执行环境。本文将探讨该项目、
> 其与 gVisor 和 Kata Containers 的集成情况，以及未来趋势。

## 简介

随着 AI 代理在企业应用中日益普及，安全执行环境的需求变得至关重要。Agent Sandbox
是 [SIG Apps](https://github.com/kubernetes/community/tree/master/sig-apps)
下的一个新 Kubernetes 项目，通过提供标准化、声明式的 API
来管理隔离的、有状态的单例工作负载——非常适合 AI 代理运行时。

**核心特性：**

- **Kubernetes 原生 Sandbox CRD 和控制器**：用于管理沙箱化工作负载的原生
  Kubernetes 抽象
- **高可扩展性**：支持数千个并发沙箱，同时实现亚秒级延迟
- **开发者友好的 SDK**：轻松集成到代理框架和工具中

## 项目概述

### 核心：Sandbox CRD

`Sandbox` 自定义资源定义（CRD）是 agent-sandbox 的核心。它提供了声明式 API
来管理单个有状态 Pod：

- **稳定身份**：每个 Sandbox 具有稳定的主机名和网络身份
- **持久存储**：Sandbox 可以配置在重启后仍然保留的持久存储
- **生命周期管理**：控制器管理 Pod 的生命周期，包括创建、计划删除、暂停和恢复

### 扩展功能

项目提供了用于高级场景的额外 CRD：

- **SandboxTemplate**：用于创建 Sandbox 的可重用模板
- **SandboxClaim**：允许用户从模板创建 Sandbox
- **SandboxWarmPool**：管理预热的 Sandbox Pod 池，实现快速分配（亚秒级启动延迟）

### 架构

```text
                              ┌─────────────────┐
                              │   K8s API       │
                              │   Server        │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐     ┌─────────────┐
                              │  Agent Sandbox  │────▶│  补充池      │
                              │   控制器         │     │  (Replenish)│
                              └────────┬────────┘     └─────────────┘
                                       │
                                       │ 从池中分配
                                       ▼
┌────────────────────────────────────────────────────────────────────┐
│                        Agent Sandbox                               │
│                  执行隔离的、低延迟任务                              │
│ ┌──────────────────┐   ┌──────────┐   ┌──────────────────────────┐ │
│ │ Agent 编排器     │──▶│ 执行器   │──▶│  任务执行                │ │
│ │       Pod        │   │ (API/SDK)│   │  Agent Sandbox          │ │
│ │                  │   │          │   │ ┌──────────────────────┐│ │
│ │ Agent 应用/框架  │   │ iStream  │   │ │执行进程              ││ │
│ │ 请求沙箱化       │   │          │   │ │  (gVisor/Kata)      ││ │
│ │ 执行环境         │   │          │   │ ├──────────────────────┤│ │
│ │                  │   │          │   │ │ 临时存储             ││ │
│ │                  │   │          │   │ ├──────────────────────┤│ │
│ │                  │   │          │   │ │ 网络策略             ││ │
│ └──────────────────┘   └──────────┘   │ └──────────────────────┘│ │
│                                        └──────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

## 运行时集成：gVisor 和 Kata Containers

Agent Sandbox 设计为**供应商中立**，支持各种运行时以提供增强的安全性和隔离性。
两个主要实现是 gVisor 和 Kata Containers。

### gVisor 集成（GKE）

[gVisor](https://gvisor.dev/)
是一个应用程序内核，在容器应用程序和宿主机内核之间提供额外的隔离层。
它拦截应用程序的系统调用并在用户空间中实现。

**GKE 集成状态：**

- **生产就绪**：gVisor 在 Google Kubernetes Engine (GKE) 中作为运行时选项可用，
  通过 `gvisor` RuntimeClass 使用
- **快照和恢复**：GKE 支持快照和恢复沙箱，实现基础设施效率和复杂的并行执行
- **性能优化**：Google 的 gVisor 团队已针对 AI 代理工作负载进行了优化，
  开销最小

**示例配置：**

```yaml
apiVersion: agents.x-k8s.io/v1alpha1
kind: Sandbox
metadata:
  name: ai-agent-sandbox
spec:
  podTemplate:
    spec:
      runtimeClassName: gvisor
      containers:
      - name: agent-runtime
        image: my-ai-agent:latest
```

### Kata Containers 集成

[Kata Containers](https://katacontainers.io/)
提供轻量级虚拟机，行为像容器但提供虚拟机的安全隔离。
每个容器在自己的轻量级虚拟机中运行，具有专用内核。

**集成状态：**

- **积极开发中**：Kata Containers 社区正在积极进行 Agent Sandbox 集成工作
- **虚拟机级别隔离**：通过硬件虚拟化提供强隔离
- **GPU 支持**：Kata 支持 GPU 直通用于 AI/ML 工作负载

**在 GKE 上使用 Kata 的示例：**

```yaml
apiVersion: agents.x-k8s.io/v1alpha1
kind: Sandbox
metadata:
  name: kata-ai-sandbox
spec:
  podTemplate:
    spec:
      runtimeClassName: kata-qemu-nvidia-gpu
      containers:
      - name: agent-runtime
        image: my-ai-agent:latest
```

**关键资源：**

- [Kata Containers Agent Sandbox 博客](https://katacontainers.io/blog/Kata-Containers-Agent-Sandbox-Integration/)
- [GKE 与 Kata Containers 示例](https://github.com/kubernetes-sigs/agent-sandbox/issues/176)

### 对比

| 特性 | gVisor | Kata Containers |
|------|--------|-----------------|
| 隔离方式 | 用户空间内核 | 硬件虚拟化 |
| 启动时间 | 更快（约100毫秒） | 较慢（约1-2秒） |
| 内存开销 | 较低 | 较高 |
| 系统调用兼容性 | 约95% | 100% |
| GPU 支持 | 有限 | 完全直通 |
| 最适合 | Web 工作负载、不受信任的代码 | GPU 工作负载、完全隔离 |

## 期望特性

Agent Sandbox 项目旨在实现：

- **强隔离**：支持 gVisor 和 Kata Containers 实现内核和网络隔离
- **深度休眠**：将状态保存到持久存储并归档 Sandbox 对象
- **自动恢复**：在网络连接时恢复沙箱
- **高效持久化**：弹性且快速配置的存储
- **内存共享**：探索在同一主机上跨 Sandbox 共享内存
- **丰富的身份和连接性**：双用户/沙箱身份和高效的流量路由
- **可编程性**：应用程序和代理可以编程方式使用 Sandbox API

## 使用场景

Agent Sandbox 设计用于：

1. **AI 代理运行时**：执行不受信任的、LLM 生成代码的隔离环境
2. **开发环境**：为开发人员提供持久的、可网络访问的云环境
3. **笔记本和研究工具**：用于 Jupyter Notebooks 等工具的持久会话
4. **有状态单 Pod 服务**：托管需要稳定身份的单实例应用程序

## 快速开始

### 安装

```bash
# 将 "vX.Y.Z" 替换为特定版本标签
export VERSION="v0.1.0"

# 安装核心组件
kubectl apply -f https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${VERSION}/manifest.yaml

# 安装扩展（可选）
kubectl apply -f https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${VERSION}/extensions.yaml
```

### 创建您的第一个 Sandbox

```yaml
apiVersion: agents.x-k8s.io/v1alpha1
kind: Sandbox
metadata:
  name: my-sandbox
spec:
  podTemplate:
    spec:
      containers:
      - name: my-container
        image: <IMAGE>
```

## 趋势和未来方向

### 行业趋势

1. **AI 代理采用增长**：随着 AI 代理变得更加自主和强大，安全执行环境变得必不可少
2. **零信任安全**：Agent Sandbox 通过提供隔离执行环境符合零信任原则
3. **云原生 AI 基础设施**：与 Kubernetes 生态系统工具（Kueue、Gateway API 等）
   集成

### 未来发展

项目路线图包括：

- **增强运行时支持**：持续改进 gVisor 和 Kata 集成
- **更好的预热池管理**：更复杂的分配策略
- **可观测性集成**：对监控和追踪的原生支持
- **多集群支持**：跨集群管理沙箱

## 资源

- **GitHub 仓库**：
  [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)
- **文档**：[agent-sandbox.sigs.k8s.io](https://agent-sandbox.sigs.k8s.io)
- **Slack**：[#sig-apps](https://kubernetes.slack.com/messages/sig-apps)
- **邮件列表**：
  [sig-apps@kubernetes.io](https://groups.google.com/a/kubernetes.io/g/sig-apps)

## 结论

Agent Sandbox 代表了在 Kubernetes 上为 AI 代理提供安全、高效执行环境的重要进步。
通过支持多种隔离运行时（gVisor 和 Kata Containers）、标准化 API
和关注开发者体验，它满足了企业环境中对沙箱化 AI 工作负载日益增长的需求。

该项目正在 SIG Apps 下积极开发，欢迎社区贡献。无论您是在构建 AI 代理、
开发环境还是任何需要隔离执行的工作负载，Agent Sandbox 都提供了 Kubernetes
原生解决方案。

---

*本博客文章基于 agent-sandbox 项目文档、社区讨论和 Kata Containers 集成博客的
信息。如需最新信息，请参阅官方项目资源。*
