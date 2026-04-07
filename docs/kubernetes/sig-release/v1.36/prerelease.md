# Kubernetes v1.36 前瞻：弃用移除与重点增强

作者：Chad Crowell、Kirti Goyal、Sophia Ugochukwu、Swathi Rao、Utkarsh Umre（2026 年 3 月 30 日）

Kubernetes v1.36 预计将在 2026 年 4 月下旬发布。本文基于当前开发状态梳理关键变化，正式发布前仍可能调整。

## Kubernetes API 的弃用与移除流程

Kubernetes 有明确的 API 弃用策略：

- 稳定版 API 只有在有新的稳定替代版本时才会被弃用。
- 被弃用后会保留一段周期并给出告警。
- 移除后需迁移到替代方案。
- 不同稳定级别（GA/Beta/Alpha）对应不同最短保留期。

所有移除都会遵循该策略，并在弃用指南中提供迁移路径。

## Ingress NGINX 退役

为优先保障生态安全，SIG Network 与 SRC 已于 2026 年 3 月 24 日退役 Ingress NGINX。之后不再发布新版本、修复或安全更新。现有部署可继续运行，安装制品（如 Helm chart、镜像）仍可获取。

参考：

- [Ingress NGINX 退役：你需要了解的内容](https://kubernetes.io/zh-cn/blog/2025/11/11/ingress-nginx-retirement/)

## v1.36 的弃用与移除

### 1) `Service.spec.externalIPs`

- v1.36 开始弃用并出现告警。
- 计划在 v1.43 完全移除。
- 该字段长期存在安全风险（如 CVE-2020-8554）。
- 建议改用 `LoadBalancer`、`NodePort` 或 `Gateway API`。

参考：

- [KEP-5707：Deprecate service.spec.externalIPs](https://kep.k8s.io/5707)

### 2) `gitRepo` 卷驱动

- 该能力自 v1.11 起已弃用。
- v1.36 起永久禁用且无法重新启用。
- 依赖该能力的工作负载需迁移到 `initContainer` 或外部 `git-sync` 等方案。

参考：

- [KEP-5040：Remove gitRepo volume driver](https://kep.k8s.io/5040)

## v1.36 重点增强

### 1) SELinux 卷标记提速（GA）

通过挂载时设置上下文替代递归重标记，提升一致性并减少 Pod 启动延迟。

- [KEP-1710：SELinux relabeling with mount options](https://kep.k8s.io/1710)

### 2) ServiceAccount Token 外部签名（GA）

kube-apiserver 可将签名委托给外部 KMS/HSM，提升安全性并简化集中式密钥管理。

- [KEP-740：External ServiceAccount token signing](https://kep.k8s.io/740)

### 3) DRA 设备污点与容忍（Beta）

允许 DRA 驱动或管理员按规则给设备打污点，避免未显式容忍的工作负载误用特定硬件。

- [KEP-5055：DRA device taints and tolerations](https://kep.k8s.io/5055)

### 4) DRA 可分区设备

支持把单个加速器划分为多个逻辑单元共享使用，提高 GPU 等高成本资源利用率。

- [KEP-4815：DRA partitionable devices](https://kep.k8s.io/4815)

## 更多信息

v1.36 的正式变更将以该版本的 CHANGELOG 与 release notes 为准。当前计划发布时间为 2026 年 4 月 22 日（周三）。

- [Kubernetes v1.36 Sneak Peek](https://kubernetes.io/blog/2026/03/30/kubernetes-v1-36-sneak-peek/)
- [v1.36 Release Highlights #2958](https://github.com/kubernetes/sig-release/discussions/2958)

## 如何参与 Kubernetes 社区

- 关注 Bluesky：`@kubernetes.io`
- 参与 [Discuss 社区讨论](https://discuss.kubernetes.io/)
- 加入 [Kubernetes Slack 社区](https://slack.k8s.io/)
- 在 [Server Fault](https://serverfault.com/questions/tagged/kubernetes) 或 [Stack Overflow](https://stackoverflow.com/questions/tagged/kubernetes) 参与问答
- 在 [Kubernetes 博客](https://kubernetes.io/blog/) 了解更多动态

## 来源

- <https://kubernetes.io/blog/2026/03/30/kubernetes-v1-36-sneak-peek/>
