---
status: Active
maintainer: pacoxu
date: 2026-04-15
tags: kubernetes, storage, csi, snapshot, checkpoint, ai-infrastructure, backup
canonical_path: docs/blog/2026-04-15/2026-04-15-volume-group-snapshot-and-cbt-for-ai-checkpoints_zh.md
source_urls:
  - https://github.com/kubernetes/website/pull/51390
  - https://github.com/kubernetes/website/pull/48456
  - https://github.com/kubernetes/enhancements/issues/3476
  - https://github.com/kubernetes/enhancements/issues/3314
  - https://github.com/kubernetes-csi/external-snapshotter
  - https://github.com/kubernetes-csi/external-snapshot-metadata
---

# 用 VolumeGroupSnapshot + CBT 改善 AI Checkpoint 备份与恢复

在 AI 训练平台里，真正贵的不是“会不会备份”，而是：

- 备份窗口太长，影响训练吞吐；
- 恢复时间太慢，影响作业 RTO；
- 全量拷贝太多，导致存储成本与网络成本持续上升。

Kubernetes storage 方向最近两条主线正好对应这些问题：

- `KEP-3476`：VolumeGroupSnapshot（多卷一致性快照）；
- `KEP-3314`：Changed Block Tracking（块级增量识别，alpha）。

## 先说结论

对 AI-Infra 来说，推荐把二者组合为一个标准流程：

1. 用 VolumeGroupSnapshot 保障多 PVC 的 crash-consistent 恢复点。
2. 用 CBT 只传输“变化块”，降低增量备份成本。
3. 恢复时优先按“组快照 + 增量链”回放，而不是每次全量回灌。

## Upstream PR 对应关系

### VolumeGroupSnapshot 线

- Alpha 博客：`website#39415`
- Beta 博客：`website#48420`
- v1beta2 博客：`website#51390`

`v1beta2` 的关键信息是：为了解决部分驱动场景下 `restoreSize` 信息缺失问题，
API 结构升级，引入了更明确的 `VolumeSnapshotInfo` 信息模型，并通过 conversion
webhook 兼容旧版对象。

### Changed Block Tracking 线

- Alpha 博客：`website#48456`

核心价值：在同一卷的两个快照之间，按 block delta 拉取变化块，不再扫描全卷。

## AI Checkpoint 的典型痛点

一个训练作业经常不是单卷：

- 模型参数卷
- 优化器状态卷
- 中间数据或日志卷

如果只做单卷快照，恢复点容易错位；如果每次全量备份，备份窗口与成本都不可控。

## 推荐架构

```text
训练任务
  -> 组快照控制器 (VolumeGroupSnapshot)
  -> 存储侧生成同一时点的多卷快照
  -> 备份系统调用 SnapshotMetadata API (CBT)
  -> 仅拉取 changed blocks
  -> 对象存储形成增量链
```

恢复路径：

```text
选择恢复点
  -> 解析对应 VolumeGroupSnapshot
  -> 为组内每个卷创建恢复 PVC
  -> 回放增量块
  -> 作业从一致性 checkpoint 重启
```

## 最小实施清单

### 1) 确认 CSI 能力

- CSI 驱动支持 group snapshot API
- CSI 驱动支持 snapshot metadata/CBT（如果要增量链）
- 部署 `external-snapshotter` 与 `external-snapshot-metadata` 相关组件

### 2) 先落地组快照

- 定义 `VolumeGroupSnapshotClass`
- 通过 label selector 把同一个训练任务的 PVC 归组
- 建立每日/每小时组快照策略

### 3) 再引入 CBT

- 打通 `GetMetadataAllocated` / `GetMetadataDelta` 客户端
- 备份管道改为“快照 + 块增量”模式
- 增加 RBAC 与 token 访问控制，避免跨租户读取元数据

## 风险与边界

1. CBT 当前是 alpha，驱动覆盖度和生态成熟度不一。
2. 不同存储后端对块追踪能力差异很大，先做小规模验证。
3. 组快照提供的是 crash consistency，不等同应用一致性。
4. 生产环境需要把“快照成功”与“恢复可用”分开验收。

## 一份可执行的推进节奏

1. 第 1 周：选定 1 个 CSI 驱动与 1 条训练流水线做试点。
2. 第 2 周：完成组快照创建、恢复演练与 RTO 基线测量。
3. 第 3 周：接入 CBT 增量链，比较全量/增量的窗口与成本。
4. 第 4 周：完善 RBAC、审计与跨租户隔离，再逐步扩大覆盖范围。

## 参考

- Kubernetes Website PR:
  [Volume Group Snapshot v1beta2](https://github.com/kubernetes/website/pull/51390)
- Kubernetes Website PR:
  [Changed Block Tracking API (alpha)](https://github.com/kubernetes/website/pull/48456)
- KEP Issue: [KEP-3476](https://github.com/kubernetes/enhancements/issues/3476)
- KEP Issue: [KEP-3314](https://github.com/kubernetes/enhancements/issues/3314)
- CSI External Snapshotter:
  [kubernetes-csi/external-snapshotter](https://github.com/kubernetes-csi/external-snapshotter)
- CSI External Snapshot Metadata:
  [kubernetes-csi/external-snapshot-metadata](https://github.com/kubernetes-csi/external-snapshot-metadata)
