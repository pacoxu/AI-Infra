---
status: Active
maintainer: pacoxu
date: 2025-12-05
tags: kubernetes, 社区, 开源, ai, ml, 贡献
canonical_path: docs/blog/2025-12-05/kubernetes-community-operations_zh.md
---

# Kubernetes 社区是如何运作的?AI 时代有哪些切入点?

## 引言

截至 2025 年 11 月,Kubernetes 社区已经发展到令人惊叹的规模:**97,800 名贡献者**、**463 万次
贡献**、**8,600 名代码审查者**参与到项目中。这个充满活力的生态系统持续演进,特别是随着 AI/ML
工作负载的快速增长,Kubernetes 正在进入新的领域。

本文将探讨 Kubernetes 社区的组织结构、运作方式,以及最重要的——在 AI 时代新人可以在哪里找到
切入点。

## 社区结构概览

Kubernetes 社区在云原生计算基金会(CNCF)的管理下运作,CNCF 是一个为项目提供资金、指导和各种
服务的非营利组织。

![社区结构](https://github.com/user-attachments/assets/fa6ad7ad-b28e-4f2d-8ffc-60fb09e3f604)

社区按层次组织:

### 1. 云原生计算基金会(CNCF)

- Kubernetes 所属的非营利组织
- 提供和管理资金及各种指导和服务
- 确保项目的可持续性和供应商中立性

### 2. 指导委员会(Steering Committee)

- 由 Kubernetes 组织成员选举产生的 **7 名成员**
- 与 CNCF 对接
- 拥有整个项目范围的权限
- 为项目设定战略方向

### 3. SIG / WG(特别兴趣小组/工作组)

- **Kubernetes 内的工作领域**
- 示例:网络、发布、文档等
- **SIG = 常设**:长期所有权领域
- **WG = 专题/临时**:有时间限制的倡议

### 4. 子项目(Subprojects)

- 由 SIG 创建
- 执行特定工作/项目的团队
- 专注的实施团队

## 贡献者阶梯

了解贡献者阶梯有助于你规划在 Kubernetes 社区的成长路径:

![贡献者阶梯](https://github.com/user-attachments/assets/ef2fc1d0-5088-4e23-9597-b94129e76db0)

### 非成员贡献者(你在这里!)

- 任何人都可以开始为 Kubernetes 贡献
- 提交代码或文档不需要成员资格

### 成员(Member)

- 项目的**活跃贡献者**
- **由两名审查者推荐**
- 在社区中拥有投票权
- 可以触发 CI 作业并使用 `/lgtm` 命令

### 审查者(Reviewer)

- **经常审查**的历史记录
- **在子项目中有作者身份**
- 批准代码质量和风格
- 可以使用 `/lgtm`(看起来不错)命令

### 批准者(Approver)

- **批准贡献以供接受**
- 子项目中**经验丰富的审查者和贡献者**
- 对代码架构有深入理解
- 可以使用 `/approve` 命令

### 子项目所有者(Subproject Owner)

- 仓库/目录的**主题专家**
- **经验丰富**,在指定范围内协助分类和指导
- 为其领域做出架构决策

### 子项目负责人(Subproject Lead)

- **为子项目设定优先级和批准提案**
- 跨所有仓库/目录对整个项目的**责任和领导**
- 与其他子项目和 SIG 协调

### SIG 主席/技术负责人(SIG Chair / Tech Lead)

- **设定优先级并管理** SIG 及其子项目
- **与指导委员会对接**
- 在社区范围的讨论中代表 SIG

**了解更多关于组织成员资格**:
<https://github.com/kubernetes/community/blob/master/community-membership.md>

## 当前的 SIG、WG 和委员会

截至 2024 年底,Kubernetes 社区已经演进了其组织结构,以更好地应对现代挑战:

![Kubernetes 社区结构](https://github.com/user-attachments/assets/c1bae44e-52fc-41c2-9b67-a965ae88ee58)

### 项目级别组

- **Architecture(架构)**:系统设计和演进
- **Contributor Experience(贡献者体验)**:改进贡献者工作流程
- **Docs(文档)**:文档和网站
- **Security Response(安全响应)**:安全漏洞处理

### 委员会

- **Code of Conduct(行为准则)**:社区行为标准
- **Steering(指导)**:整体项目治理

### 横向 SIG(跨领域关注点)

- **API Machinery**: 核心 API 基础设施
- **Auth**: 认证和授权
- **CLI**: 命令行工具(kubectl)
- **Instrumentation**: 指标和监控
- **Windows**: Windows 容器支持
- **Structured Logging**: 日志基础设施
- **Long Term Support (LTS)**: 长期支持策略
- **AI Conformance**: AI 工作负载一致性测试

### 纵向 SIG(功能领域)

- **Apps**: 应用生命周期管理
- **Autoscaling**: 水平和垂直 Pod 自动扩缩容
- **Cloud Provider**: 云提供商集成
- **Cluster Lifecycle**: 集群创建和管理
- **Storage**: 持久化存储解决方案
- **etcd**: 键值存储操作
- **Network**: 网络功能和 CNI
- **Node**: 节点生命周期和资源管理
- **Scheduling**: Pod 调度和资源分配

### 工作组(临时/专题)

- **Checkpoint Restore**: 容器检查点
- **Node Lifecycle**: 节点操作和生命周期
- **AI Gateway**: AI 推理网关解决方案
- **AI Integration**: AI 工作负载集成
- **Device Management**: 硬件设备管理
- **etcd Operator**: etcd operator 开发
- **Batch**: 批处理工作负载
- **Serving**: 服务工作负载(推理)
- **Data Protection**: 数据备份和恢复

**新工作组表明了新兴领域**,具有活跃的开发和贡献机会。

## Kubernetes 中的 AI/ML 切入点

AI/ML 工作负载的快速增长为 Kubernetes 社区创造了令人兴奋的新机会。以下是专注于 AI/ML 的关键
工作组:

![AI/ML 工作组](https://github.com/user-attachments/assets/504acacc-77a6-43dc-b5d4-ff243e7d0b68)

### WG Batch 和 Serving:以工作负载为中心

这些工作组专注于 AI/ML 的基本工作负载模式:

- **WG Batch**: 训练工作负载、分布式训练、gang 调度
- **WG Serving**: 推理工作负载、模型服务、自动扩缩容

**关键倡议:**

- JobSet 用于分布式训练协调
- LeaderWorkerSet 用于推理工作负载
- Gang 调度用于全有或全无的放置
- GPU 的动态资源分配

### WG Device Management:硬件驱动

专注于管理 AI 工作负载的专用硬件:

- GPU 管理和共享
- TPU 集成
- 自定义加速器支持
- 动态资源分配(DRA) API

**关键技术:**

- NVIDIA GPU Operator
- 节点资源接口(NRI)
- Device Plugin 框架演进
- DRA 驱动程序和资源声明

### WG AI Conformance:鸟瞰视图

提供 AI 工作负载兼容性的整体视图:

- AI 工作负载的一致性测试
- Kubernetes 上 AI 的最佳实践
- 集成模式验证
- 性能基准测试

### WG AI Gateway:产品驱动

专注于生产 AI 部署模式:

- LLM 推理的 API 网关
- 多模型服务
- 流量路由和负载均衡
- 成本优化策略

### WG AI Integration:跨领域

协调 AI 工作的总括组:

- 在所有与 AI 相关的工作组之间进行协调
- 确保一致的 API 和模式
- 推动社区对齐
- 识别差距和机会

**关系:**

- WG Batch 和 WG Serving 输入到 WG AI Integration
- WG Device Management 为所有工作负载提供基础设施
- WG AI Gateway 基于 WG Serving 模式构建
- WG AI Conformance 验证来自所有组的解决方案

## 入门:新贡献者入门

Kubernetes 社区为新贡献者提供了出色的资源:

### 新贡献者入门

**官方指南**:
<https://github.com/kubernetes/community/tree/master/mentoring/new-contributor-orientation>

入门计划包括:

1. **了解项目**
   - 项目历史和治理
   - 社区价值观和行为准则
   - 沟通渠道(Slack、邮件列表、会议)

2. **技术入门**
   - 开发环境设置
   - 测试基础设施
   - CI/CD 管道理解

3. **贡献工作流程**
   - 查找好的第一个 issue
   - Pull request 流程
   - 代码审查期望
   - 与 SIG 合作

4. **社区参与**
   - 参加 SIG 会议
   - 参与讨论
   - 寻找导师
   - 建立关系

### AI/ML 贡献者资源

如果你对 Kubernetes 上的 AI/ML 工作负载感兴趣:

1. **加入相关的 Slack 频道**
   - #wg-batch
   - #wg-serving
   - #wg-device-management
   - #sig-scheduling
   - #sig-node

2. **参加 WG 会议**
   - 查看社区日历: <https://kubernetes.dev/>
   - 会议对所有人开放
   - 是了解当前优先事项的好方法

3. **探索好的第一个 issue**
   - 寻找 `good-first-issue` 标签
   - AI 相关的仓库通常需要文档
   - 测试和验证总是需要的

4. **关注 AI/ML 倡议**
   - 动态资源分配(DRA)
   - Gang 调度
   - LeaderWorkerSet (LWS)
   - JobSet
   - AI 一致性测试

## 更多倡议

Kubernetes 社区非常活跃,除了我们介绍的内容之外,还有许多正在进行的倡议。AI/ML 领域继续快速
演进,新的提案、增强和集成正在定期讨论。

一些值得关注的领域:

- **无服务器 AI 推理**模式
- AI 工作负载的**多租户**
- GPU 工作负载的**成本优化**
- 分布式训练的**可观测性**
- AI 模型和数据的**安全性**
- **边缘 AI** 部署模式

## 结论

Kubernetes 社区为各个级别的贡献者提供了一个结构良好、包容性强的环境。随着 AI/ML 工作负载的
爆炸性增长,现在比以往任何时候都有更多的机会做出有意义的贡献。

无论你对核心调度改进、GPU 管理、分布式训练还是推理服务感兴趣,Kubernetes 社区都有你的位置。

**今天就开始你的旅程:**

- 访问 <https://kubernetes.dev/> 获取社区资源
- 加入 Slack 工作区
- 选择一个与你兴趣一致的工作组
- 打个招呼,开始贡献!

## 参考资料

- **Kubernetes Community**: <https://kubernetes.dev/>
- **New Contributor Orientation**:
  <https://github.com/kubernetes/community/tree/master/mentoring/new-contributor-orientation>
- **Community Membership**:
  <https://github.com/kubernetes/community/blob/master/community-membership.md>
- **Kubernetes 开源入门手册**:
  <https://mp.weixin.qq.com/s/-htUKeQLF6_m6_bQjDxGMw>
- **Kubernetes社区是如何运作的**:
  <https://mp.weixin.qq.com/s/KS0IGr8XeNwcWTgl9AFAUg>

## 视频资源

![KCD China 视频](https://github.com/user-attachments/assets/cf2c1e26-bec9-414e-b2f5-b6e97c20ff0e)

### KCD Shanghai 2024: 云原生新手和开源教育分论坛 02 - 技术 or 非技术,参与 Kubernetes 社区的正确姿势

KCD-China Bilibili 频道: <https://space.bilibili.com/472621817>

---

*本博客文章是 AI-Infra 学习路径的一部分。有关 AI 基础设施和 Kubernetes 的更多资源,请访问
[主仓库](../../../README.md)。*
