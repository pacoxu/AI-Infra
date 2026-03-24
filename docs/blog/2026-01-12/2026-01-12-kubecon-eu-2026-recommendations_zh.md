---
status: Active
maintainer: pacoxu
last_updated: 2026-01-12
tags: kubecon, cloudnativecon, europe, ai-infrastructure, kubernetes, recommendations
---

# KubeCon + CloudNativeCon Europe 2026 主题推荐

## 会议链接

https://kccnceu2026.sched.com/

https://colocatedeventseu2026.sched.com/

## CNCF 发布 KubeCon + CloudNativeCon Europe 2026 日程

**2025年12月10日** — Cloud Native Computing Foundation (CNCF) 正式公布了 KubeCon + CloudNativeCon Europe 2026
的完整日程。本次大会将于 2026 年 3 月 23-26 日在荷兰阿姆斯特丹举办，汇聚全球云原生社区的开发者、技术领袖和终端用户，
共同探讨云原生技术的最新进展和未来趋势。

### 会议亮点

KubeCon + CloudNativeCon Europe 2026 将延续往届的成功经验，为参会者提供丰富多样的技术内容：

- **主题演讲 (Keynotes)：** 来自云原生领域的顶级专家和行业领袖将分享最新洞察和技术愿景
- **技术分会 (Breakout Sessions)：** 涵盖 Kubernetes、容器运行时、服务网格、可观测性、AI/ML 等众多领域的深度技术分享
- **教程 (Tutorials)：** 动手实践环节，帮助参会者掌握云原生技术的实际应用
- **闪电演讲 (Lightning Talks)：** 快速分享创新想法和实践经验
- **协同活动 (Co-located Events)：** 各种社区聚会、项目会议和专题研讨会

### 大会主题

本次 KubeCon + CloudNativeCon Europe 2026 将重点关注以下领域：

1. **AI/ML 基础设施：** 在 Kubernetes 上构建和运行 AI 工作负载
2. **平台工程：** 构建开发者友好的内部平台
3. **安全性：** 云原生安全最佳实践和工具
4. **可观测性：** 监控、追踪和日志分析
5. **多集群和边缘计算：** 分布式架构和边缘场景
6. **FinOps 和成本优化：** 云资源的高效利用

### 注册信息

- **会议地点：** 荷兰 阿姆斯特丹
- **会议日期：** 2026 年 3 月 23-26 日
- **详细信息：** https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/

## AI 基础设施推荐主题

以下是我们精选的几个与 AI 基础设施相关的优质主题，涵盖大规模工作流编排、LLM 推理优化和智能路由等前沿话题。

### 1. 赋能自主化：比亚迪使用 Argo Workflows 驯服百万任务规模的实践之路

**演讲者：** Shuangkun Tian (Alibaba Cloud) & Zhang Bao (BYD)

**时间：** Monday March 23, 2026 10:50 - 11:15 CET

随着比亚迪自动驾驶业务的快速扩展，其平台每天需要处理数以千万计的数据记录，要求高效的数据清洗、标注和修复流水线。
比亚迪从 Airflow 迁移到 Kubernetes 原生的 Argo Workflows，构建了一个能够管理 3000+ GPU 并每天运行超过 100
万个数据任务的系统。

**演讲将分享以下挑战和解决方案：**

- **GPU 利用率优化：** 优化千 GPU 集群的资源利用，实现多租户资源共享
- **高并发处理：** 通过先进的并发控制，支撑数百万任务的稳定运行，提升吞吐量
- **超大规模稳定性：** 解决 30 万+ 工作流规模下的调度挑战，如 informer 更新延迟和控制器内存飙升
- **社区贡献：** 向 Argo Workflows 项目上游贡献修复和可扩展性改进

**参会者将学到如何编排大规模 GPU 密集型工作流，并确保系统在大规模下的稳定性。**

<img src="https://github.com/user-attachments/assets/8b23e29b-9f52-4ab1-8f63-c4b87ab1b289" width="800"
alt="BYD Argo Workflows">

### 2. 📚 教程：KV-Cache 带来的可感知收益——在 Kubernetes 上构建具备 AI 感知的 LLM 路由

**演讲者：** Tyler Michael Smith (Red Hat), Kay Yan (DaoCloud), Danny Harnik (IBM), Michal Malka (IBM) &
Maroon Ayoub (IBM)

**时间：** Thursday March 26, 2026 11:00 - 12:15 CET

**地点：** Elicium Ballroom 1

每个 LLM 请求都携带着不可见的状态：KV-cache（键值缓存）。命中缓存，响应速度可以提升 10 倍，成本降低 50 倍。
错过缓存，你将重新计算刚刚完成的工作。然而，Kubernetes 默认的负载均衡是缓存无感知的，会将相关请求分散到不同的
pod 上，破坏局部性。结果？你的 AI 工作负载变得更慢，成本也远高于应有的水平。

**在这个动手教程中，我们将解决这个问题。**

参会者将部署一个分布式 vLLM 集群，对其性能进行基准测试，并可视化缓存无感知路由如何浪费 GPU 周期。然后，
我们将用 Kubernetes Gateway API（Inference Extension）替换默认 Service，并部署 llm-d —— 一个
Kubernetes 原生的分布式 LLM 推理框架。通过重新运行相同的基准测试，你将看到延迟和吞吐量如何随着
prefix-reuse（前缀重用）成为一等公民而发生转变。你将获得一个可工作的实验环境、仪表板，
以及在任何生产 AI 栈中构建缓存感知路由的心智模型。

<img src="https://github.com/user-attachments/assets/48d838fc-aa02-40e3-b64d-197e53f2df02" width="800"
alt="KV-Cache Tutorial">

### 3. Route, Serve, Adapt, Repeat：Kubernetes 上 AI 推理工作负载的自适应路由

**演讲者：** Nir Rozenbaum (IBM) & Kellen Swain (Google)

**时间：** Wednesday March 25, 2026 11:45 - 12:15 CET

**地点：** Auditorium

在 Kubernetes 上运行推理工作负载可能成本高昂且极度缓慢。

当今的推理路由策略，如流量分割、节点亲和性或会话粘性，都是静态的。一旦定义，它们就会忽略不断变化的负载、
队列堆积和缓存局部性。

然而，推理工作负载是动态的：请求各不相同，缓存状态会变化，集群条件也在不断演变。静态路由策略根本无法跟上，
导致延迟飙升和 GPU 周期的浪费。

通过 Kubernetes Gateway API Inference Extension，我们引入了针对推理的自适应路由策略，
由队列长度和缓存利用率等实时信号驱动。系统通过持续适应，在缓存效率和负载分配之间取得平衡，
降低延迟，提高 GPU 利用率，并大规模降低成本。

**参会者将了解为什么静态路由策略限制了推理性能，并通过基准测试看到自适应路由在 Kubernetes Gateway API
Inference Extension 中带来的延迟、效率和成本优势。**

<img src="https://github.com/user-attachments/assets/170a11a3-7b98-4d7c-8002-a3f7bf6a7dda" width="800"
alt="Adaptive Routing">

### 4. 重新定义 LLM 推理 SLI/SLO：从"请求"到"token/GPU"的端到端观测

**演讲者：** Christopher Nuland (Red Hat) & Hilliary Lipsig (Red Hat)

**时间：** Thursday March 26, 2026 14:30 - 15:00 CET

**地点：** Hall 7 | Room A

大语言模型 (LLM) 正在重塑应用交付，为 SRE 带来了全新的运维挑战。传统的 CPU 或请求延迟等指标已不再足够。
延迟现在以每秒 token 数来衡量，可靠性取决于路由效率和缓存命中率。在混合云环境中，推理流水线横跨网关、
调度器、缓存和共享后端，使可观测性和 SLO 管理变得复杂。

**本次演讲将探讨生产 LLM 不断演进的 SLO/SLI，涵盖以下指标：**

- Time-to-First-Token (TTFT，首 token 时间)
- 缓存命中率
- 路由延迟
- GPU 利用率

我们将展示 vLLM 和 llm-d 如何为可扩展、可观测的推理提供基础能力：vLLM 用于高性能批处理和缓存，
llm-d 用于智能调度和 KV-cache 感知路由。参会者将学习如何定义新的 SLO，使用 Prometheus、
OpenTelemetry 和 Grafana 对分布式推理进行监控，并将 LLM 遥测数据集成到 Kubernetes SRE 工作流中。

<img src="https://github.com/user-attachments/assets/397e4b37-5ac4-42ff-9996-f69f651bda38" width="800"
alt="Redefining LLM Inference SLI/SLO">

## 总结

KubeCon + CloudNativeCon Europe 2026 将是云原生社区的又一次盛会，特别是在 AI 基础设施领域，
将有众多精彩的技术分享和实践案例。以上推荐的主题涵盖了从大规模工作流编排到 LLM 推理优化的各个方面，
相信会为从事 AI 基础设施工作的工程师带来丰富的启发和实用的经验。

期待在伦敦与大家相见！

## 参考资料

- KubeCon + CloudNativeCon Europe 2026 主会场：https://kccnceu2026.sched.com/
- 协同活动日程：https://colocatedeventseu2026.sched.com/
- CNCF 官方公告：https://www.cncf.io/announcements/2025/12/10/cncf-unveils-schedule-for-kubecon-cloudnativecon-europe-2026/
- 注册链接：https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/
