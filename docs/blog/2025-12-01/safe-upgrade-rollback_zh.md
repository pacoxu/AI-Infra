---
status: Active
maintainer: pacoxu
date: 2025-12-01
tags: kubernetes, upgrade, rollback, emulation-version, compatibility
canonical_path: docs/blog/2025-12-01/safe-upgrade-rollback_zh.md
---

# Kubernetes 安全升级与回滚：模拟版本与兼容性

## 简介

Kubernetes 升级一直是单向操作。一旦将控制平面升级到新版本，官方不支持回滚。这对于运行大规模
集群的组织来说是一个重大痛点，因为升级失败可能会产生严重后果。

随着**模拟版本（Emulation Version）**和**最低兼容性版本（Minimum Compatibility
Version）**的引入，Kubernetes 现在提供了更安全的升级路径和强大的回滚能力。这对集群运维人员
和平台工程师来说是一个重大突破。

## GKE 大规模可靠性

Google Kubernetes Engine (GKE) 已经实现了卓越的可靠性：

<img width="600" alt="GKE 可靠性"
  src="https://github.com/user-attachments/assets/f129580f-0c8d-4cc4-8562-59bc819543a0" />

- **99.98% 升级成功率**，覆盖所有 GKE 小版本和补丁升级
- **97% 的 GKE 集群**运行在最新的 3 个 Kubernetes 版本上

这些数字展示了升级过程的稳定性和成熟度，但即使成功率如此之高，剩余的 0.02% 失败对于大型组织
来说可能是至关重要的。这就是为什么回滚能力是必不可少的。

## 未来：跨版本升级和优雅降级

<img width="600" alt="前进之路"
  src="https://github.com/user-attachments/assets/143ca7eb-1083-461a-bb79-babf700b2950" />

Kubernetes 升级的未来之路包括：

- **跨版本升级**：想象一下……一年只需要升级一次
- **优雅降级**：能够在不丢失数据的情况下回滚

*注意：这不是停止升级的借口！*定期升级对于安全补丁和功能改进仍然很重要。

## Kubernetes 回滚终于来了

<img width="800" alt="Kubernetes 回滚"
  src="https://github.com/user-attachments/assets/1243b8ac-bb61-4a01-b083-45256bcfb6d4" />

关键创新是将**二进制版本**和**模拟版本**分离：

### 二进制版本升级/降级

- 二进制：1.32 → 二进制：**1.33**
- 模拟：1.32 → 模拟：1.32

使用这种方法：

- Kubernetes API 保持完全相同
- 所有功能保持完全相同（无论弃用与否，都不会移除或添加任何功能）
- **从根本上安全地回滚**

### 模拟版本升级

- 二进制：1.33 → 二进制：1.33
- 模拟：1.32 → 模拟：**1.33**

使用这种方法：

- 新的 API 和功能变得可用
- 弃用生效

## 工作原理：模拟版本和兼容性版本

### `--emulation-version`（Kubernetes 1.31+）

`--emulation-version` 标志允许 API 服务器模拟先前 Kubernetes 版本的行为，即使运行的是
较新的二进制文件。

```bash
# 运行 1.33 二进制文件但表现得像 1.32
kube-apiserver --emulation-version=1.32
```

主要优势：

- **细粒度升级步骤**：先升级二进制文件，然后启用新功能
- **强大的回滚能力**：可以降级二进制文件而不会出现数据不兼容

### `--min-compatibility-version`（Kubernetes 1.35+）

`--min-compatibility-version` 标志在保持向后兼容性的同时，能够更快地开发和采用新功能。

```bash
# 确保与 1.34 客户端兼容
kube-apiserver --min-compatibility-version=1.34
```

主要优势：

- **更快的功能开发**：可以开发新功能而不用担心破坏旧客户端
- **更快的功能采用**：用户可以更快地采用新功能

## 更安全的升级，更安全的 Kubernetes

<img width="600" alt="更安全的升级"
  src="https://github.com/user-attachments/assets/02530976-ead6-4cc4-8144-6501a485200b" />

### 模拟版本

- 细粒度升级步骤
- 强大的回滚能力

### 最低兼容性版本

- 更快的功能开发
- 更快的功能采用

## 升级过程中的不同就绪阶段

<img width="600" alt="就绪阶段"
  src="https://github.com/user-attachments/assets/6744abd9-336e-45cf-a051-1d346eeba6a9" />

升级过程可以分为三个阶段：

### 阶段 1：后悔还来得及

- 二进制：N
- 模拟：N-1
- 最低兼容：N-1

在这个阶段，您已经升级了二进制文件，但仍在模拟先前版本。您可以安全地回滚到先前的二进制版本。

### 阶段 2：新篇章

- 二进制：N
- 模拟：N
- 最低兼容：N-1

在这个阶段，您已经开始使用版本 N 的新功能。回滚仍然可能，但可能需要对使用新功能的工作负载
进行一些手动干预。

### 阶段 3：无法回头

- 二进制：N
- 模拟：N
- 最低兼容：N

在这个阶段，您已经完全提交到版本 N。所有客户端和工作负载都应该与版本 N 兼容。

## 安全升级最佳实践

### 1. 分阶段发布

```bash
# 步骤 1：升级二进制文件，保持模拟版本
kube-apiserver --emulation-version=1.32

# 步骤 2：验证集群健康状况和工作负载

# 步骤 3：升级模拟版本
kube-apiserver --emulation-version=1.33

# 步骤 4：验证新功能和弃用情况
```

### 2. 升级前检查清单

- 审查已弃用的 API 和功能门控
- 在暂存环境中针对新版本测试工作负载
- 确保所有 operator 和 controller 兼容
- 记录回滚程序

### 3. 回滚程序

```bash
# 如果模拟版本升级后出现问题：
# 首先回滚模拟版本
kube-apiserver --emulation-version=1.32

# 如果二进制升级后问题仍然存在：
# 回滚到先前的二进制文件
# （仅在模拟版本匹配时安全）
```

## KEP-4330：兼容性版本

有关详细技术信息，请参阅 Kubernetes 增强提案：

- [KEP-4330：兼容性版本](https://github.com/kubernetes/enhancements/tree/master/keps/sig-architecture/4330-compatibility-versions)

### 时间线

| 版本 | 功能 |
| --- | --- |
| 1.31 | `--emulation-version` 引入（Alpha） |
| 1.34 | `--emulation-version` 升级（Beta） |
| 1.35 | `--min-compatibility-version` 引入 |

## 使用场景

### 大型企业集群

对于运行数百或数千个集群的组织，回滚能力在升级周期中提供了安全网。这对于以下场景尤其重要：

- 具有严格 SLA 的金融服务
- 需要高可用性的医疗系统
- 高峰流量期间的电子商务平台

### AI/ML 工作负载

AI 训练作业通常运行数天或数周。能够在不中断长时间运行的工作负载的情况下回滚升级是非常宝贵的。

### 多租户平台

平台提供商可以升级其控制平面，同时给租户时间将其工作负载迁移到使用新 API。

## 结论

模拟版本和兼容性版本的引入代表着 Kubernetes 集群管理的重大进步。通过将二进制升级与功能激活
分离，运维人员现在拥有：

1. **更安全的升级**：测试新二进制文件而不启用新功能
2. **强大的回滚**：返回到先前的行为而不会丢失数据
3. **渐进式采用**：按照自己的节奏启用新功能
4. **更好的规划**：清晰的升级就绪阶段

这对于 AI 基础设施尤其重要，因为稳定性和可预测性对于运行昂贵的 GPU 工作负载至关重要。

---

## 参考资料

### KEP 和文档

- [KEP-4330：兼容性版本](https://github.com/kubernetes/enhancements/tree/master/keps/sig-architecture/4330-compatibility-versions)
- [Google Cloud 博客：Kubernetes 获得小版本回滚](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-gets-minor-version-rollback)

### 会议演讲

- [KubeCon NA 2025 Keynote：GKE 大规模可靠性](https://www.youtube.com/watch?v=kPUdlmov5TM&list=PLj6h78yzYM2OPbGEIqJk2AT25wGu9mY8V&index=5&t=495s)（Navigating
  the Multi-Version Kubernetes Universe: How Emulation Version Shapes Your...
  - Siyuan Zhang）

### 相关主题

- [Kubernetes 学习计划](../../kubernetes/learning-plan.md)
- [调度优化](../../kubernetes/scheduling-optimization.md)

---

**作者**：AI 基础设施学习路径  
**日期**：2025 年 12 月 1 日  
**标签**：#kubernetes #升级 #回滚 #模拟版本 #兼容性
