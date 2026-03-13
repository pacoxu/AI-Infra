---
status: Active
maintainer: pacoxu
date: 2025-11-26
tags: kubernetes, cgroup, linux, container-runtime, migration
canonical_path: docs/blog/2025-11-26/cgroup-v2_zh.md
---

# 迁移到 cgroup v2：Kubernetes 用户需要了解的内容

## 引言

随着 Kubernetes 1.35 的发布，cgroup v1 已被正式废弃。这标志着 Kubernetes 生态系统向更
现代、更高效的 cgroup v2 接口过渡的重要里程碑。在本篇博客中，我们将探讨 cgroup v2 带来了
什么，为什么要进行迁移，以及您需要做哪些准备。

### 关键公告

- **Kubernetes 1.31**：cgroup v1 支持进入
  [维护模式](https://kubernetes.io/blog/2024/08/14/kubernetes-1-31-moving-cgroup-v1-support-maintenance-mode/)
- **Kubernetes 1.35**：cgroup v1
  [正式废弃](https://github.com/kubernetes/enhancements/issues/5573)。
  移除将遵循 Kubernetes 废弃策略
- **容器运行时**：[containerd](https://github.com/containerd/containerd/issues/12443)
  和 [moby (Docker)](https://github.com/moby/moby/issues/51111)
  也在废弃 cgroup v1 支持

## 什么是 cgroups？

控制组（cgroups）是 Linux 内核的一个功能，允许您在系统上运行的用户定义的任务（进程）组
之间分配资源——如 CPU 时间、系统内存、网络带宽，或这些资源的组合。

### cgroup v1：最初的设计

cgroup v1 由 Google 开发，于 2008 年 1 月合并到 Linux 内核 2.6.24 中。它引入的资源
控制器（子系统）是逐步添加的：

| 内核版本 | 年份 | 新增的控制器 |
|---------|------|------------|
| 2.6.24 | 2008 | cpu, cpuacct, cpuset |
| 2.6.25 | 2008 | memory |
| 2.6.26 | 2008 | devices |
| 2.6.28 | 2008 | freezer |
| 2.6.29 | 2009 | netcls |
| 2.6.33 | 2010 | blkio |
| 2.6.39 | 2011 | perf_event |
| 3.3 | 2012 | net_prio |
| 3.5 | 2012 | hugetlb |
| 4.3 | 2015 | pids |
| 4.11 | 2017 | rdma |

### cgroup v1 的问题

尽管取得了成功，cgroup v1 仍存在几个众所周知的限制：

1. **控制器层级分离**：每个控制器必须单独处理。拥有不同层级的灵活性在实践中并未被使用
2. **内存子系统集成**：与某些内核子系统（如内存）的集成不够理想
3. **不安全的委派**：将子树委派给权限较低的进程是不安全的
4. **无资源预留**：没有资源分配保证机制
5. **接口不一致**：不同子系统之间存在不一致性
6. **非原子操作**：创建、删除或移动 cgroup 必须为每个控制器单独执行
7. **OOM Killer 问题**：OOM killer 不感知 cgroup；来自不同容器/cgroup 的进程可能
   同时被终止

### cgroup v2：统一层级

cgroup v2 于 2016 年 3 月随 Linux 内核 4.5 正式发布。它引入了统一层级，解决了 v1 的
许多限制：

| 内核版本 | 年份 | 新增的控制器 |
|---------|------|------------|
| 4.5 | 2016 | io, memory, pids |
| 4.11 | 2017 | perf_event, rdma |
| 4.15 | 2018 | cpu |
| 5.0 | 2019 | cpuset |
| 5.2 | 2019 | freezer |
| 5.6 | 2020 | hugetlb |

## cgroup v1 与 v2 层级对比

### v1：多重层级

在 cgroup v1 中，每个控制器都有自己的层级：

```text
/sys/fs/cgroup/
├── cpu/
│   └── kubepods/
│       └── burstable/
│           └── pod1/
│               ├── container_main/
│               │   ├── cpu.shares
│               │   └── cpu.cfs_quota_us
│               └── sidecar/
│                   ├── cpu.shares
│                   └── cpu.cfs_quota_us
└── memory/
    └── kubepods/
        └── burstable/
            └── pod1/
                ├── container_main/
                │   └── memory.limit_in_bytes
                └── sidecar/
                    └── memory.limit_in_bytes
```

### v2：统一层级

在 cgroup v2 中，所有控制器共享单一层级：

```text
/sys/fs/cgroup/
└── kubepods.slice/
    └── kubepods-burstable.slice/
        └── kubepods-burstable-pod1.slice/
            ├── cri-containerd-container_main.scope/
            │   ├── cpu.weight
            │   ├── cpu.max
            │   └── memory.max
            └── cri-containerd-container_sidecar.scope/
                ├── cpu.weight
                ├── cpu.max
                └── memory.max
```

## cgroup v2 的关键改进

### 1. 统一层级

所有资源控制器组织在单一树结构中，简化了管理并消除了不同控制器层级之间的不一致性。

### 2. 改进的 CPU 控制器

cgroup v2 中的 CPU 控制器使用 `cpu.weight`（范围 1-10000，默认 100）代替
`cpu.shares`（范围 2-262144，默认 1024）：

```text
# cgroup v1
cpu.shares = 1024  (相对权重)
cpu.cfs_quota_us = 100000  (硬限制)
cpu.cfs_period_us = 100000  (周期)

# cgroup v2
cpu.weight = 100  (相对权重，更直观的刻度)
cpu.max = "100000 100000"  (配额 周期 格式)
```

### 3. 增强的内存控制器

cgroup v2 引入了分级内存控制模型：

- **memory.min**：硬内存保护。低于此阈值的内存永远不会被回收，即使在内存压力很大的情况下
- **memory.low**：软内存保护。如果其他地方有可回收内存，低于此阈值的内存将受到保护不被回收
- **memory.high**：内存节流阈值。当内存超过此限制时，内核会积极回收内存。这是一个软限制
- **memory.max**：硬内存限制。如果内存使用量达到此限制，将触发 OOM killer

与 v1 的简单硬限制相比，这种分级方法提供了更精细的内存管理控制。

### 4. 压力失速信息（PSI）

cgroup v2 中最重要的新增功能之一是压力失速信息（PSI），它提供资源争用的指标：

```bash
# 检查 CPU 压力
cat /sys/fs/cgroup/kubepods.slice/cpu.pressure
# 输出: some avg10=0.00 avg60=0.00 avg300=0.00 total=0
#       full avg10=0.00 avg60=0.00 avg300=0.00 total=0

# 检查内存压力
cat /sys/fs/cgroup/kubepods.slice/memory.pressure
# 输出: some avg10=0.00 avg60=0.00 avg300=0.00 total=0
#       full avg10=0.00 avg60=0.00 avg300=0.00 total=0

# 检查 I/O 压力
cat /sys/fs/cgroup/kubepods.slice/io.pressure
# 输出: some avg10=0.00 avg60=0.00 avg300=0.00 total=0
#       full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

PSI 指标包括：

- **some**：至少有一个任务在资源上停滞的时间百分比
- **full**：所有任务都在资源上停滞的时间百分比
- **avg10/avg60/avg300**：10秒、60秒和300秒窗口的平均值

### 5. 安全委派

cgroup v2 通过以下方式引入了适当的委派支持：

- `cgroup.subtree_control`：控制在子 cgroup 中启用哪些控制器
- 适当的权限模型用于非特权 cgroup 管理
- 安全地委派给容器和 rootless 运行时

### 6. 原子操作

在 cgroup v2 中，创建 cgroup 会自动启用所有控制器，消除了每个控制器单独操作的需要。

## Kubernetes 与 cgroup v2 时间线

- **Kubernetes 1.19**：首个支持 cgroup v2 的版本
- **Kubernetes 增强提案 (PR #1370)**：2020 年 2 月被接受
- **Kubernetes 1.25**：cgroup v2 支持正式稳定（GA）
- **Kubernetes 1.31**：cgroup v1 支持进入维护模式
- **Kubernetes 1.35**：cgroup v1 正式废弃

## 迁移指南

### 步骤 1：检查当前 cgroup 版本

```bash
# 检查挂载的 cgroup 版本
mount | grep cgroup

# 对于 cgroup v1，您会看到多个挂载，如：
# cgroup on /sys/fs/cgroup/cpu type cgroup (...)
# cgroup on /sys/fs/cgroup/memory type cgroup (...)

# 对于 cgroup v2，您会看到单一的统一挂载：
# cgroup2 on /sys/fs/cgroup type cgroup2 (...)

# 或检查文件系统类型
stat -fc %T /sys/fs/cgroup/
# cgroup2fs 表示 v2，tmpfs 表示 v1
```

### 步骤 2：验证 Linux 发行版支持

大多数现代 Linux 发行版默认启用 cgroup v2：

| 发行版 | 默认启用 cgroup v2 的版本 |
|-------|------------------------|
| Fedora | 31 (2019) |
| Arch Linux | 2021 年 4 月 |
| openSUSE Tumbleweed | ~2021 |
| Debian | 11 (Bullseye, 2021) |
| Ubuntu | 21.10 (20.04 起可用 cgroups v2) |
| RHEL | 9 (2022) |
| Rocky Linux | 9 (2022) |
| AlmaLinux | 9 (2022) |

### 步骤 3：升级容器运行时依赖

迁移到 cgroup v2 时，Kubernetes 建议升级您的容器运行时依赖：

- **runc**：升级到 **1.3.2 或更高版本**
- **crun**：升级到 **1.23 或更高版本**

> **重要提示**：这些版本包含生态系统正在采用的新 `cpu.weight` 计算公式。详情请参阅即将
> 发布的博客文章 [kubernetes/website#52793](https://github.com/kubernetes/website/pull/52793)
> 和问题 [kubernetes/kubernetes#131216](https://github.com/kubernetes/kubernetes/issues/131216)。

### 步骤 4：启用 cgroup v2（如需要）

如果您的系统未启用 cgroup v2，请在内核启动参数中添加以下内容：

```text
systemd.unified_cgroup_hierarchy=1
```

对于基于 GRUB 的系统：

```bash
# 编辑 /etc/default/grub
GRUB_CMDLINE_LINUX="systemd.unified_cgroup_hierarchy=1"

# 更新 GRUB
sudo update-grub  # Debian/Ubuntu
# 或
sudo grub2-mkconfig -o /boot/grub2/grub.cfg  # RHEL/CentOS
```

### 步骤 5：验证 Kubernetes 兼容性

确保您的 Kubernetes 组件兼容：

- kubelet 必须配置为使用 cgroup v2
- 容器运行时（containerd、CRI-O）必须支持 cgroup v2
- 所有节点组件应更新到兼容版本

## kubeadm 用户的重要注意事项

> **⚠️ kubeadm 升级过程警告**
>
> 使用 kubeadm 管理 Kubernetes 集群升级时，请注意以下升级顺序：
>
> 1. **首先升级控制平面**：在此阶段，kubelet 仍运行旧版本。您将看到关于 cgroup v1 的
>    **警告消息**，而不是错误
> 2. **其次升级 kubelet**：这是关键阶段。如果您在控制平面升级期间忽略了警告，而您的节点
>    使用 cgroup v1，则升级后 kubelet 将**无法启动**（除非您修改了 `FailCgroupV1` 配置）
>
> **需要采取的行动**：不要忽略控制平面升级期间的 cgroup v1 警告。在将 kubelet 升级到
> Kubernetes 1.35 或更高版本之前，确保您的节点已迁移到 cgroup v2。
>
> 更多详情，请参阅
> [kubernetes/system-validators#58](https://github.com/kubernetes/system-validators/issues/58)。

## 检查容器运行时支持

### containerd

```bash
# 检查 containerd 版本和配置
containerd --version

# 验证配置中的 cgroup 驱动
cat /etc/containerd/config.toml | grep -i cgroup
# 应显示: SystemdCgroup = true
```

### CRI-O

```bash
# 检查 CRI-O 版本
crio --version

# 验证 cgroup 配置
cat /etc/crio/crio.conf | grep -i cgroup
```

## 常见问题和故障排除

### 问题 1：内存指标差异

从 cgroup v1 迁移到 v2 时，您可能会注意到内存指标报告的差异。这是由于 cgroup v2 中内存
记账方式的变化。

请参阅博客文章
[揭开K8s适配CgroupV2内存虚高的迷局](https://mp.weixin.qq.com/s?__biz=MzI1MzE0NTI0NQ==&mid=2650492905&idx=1&sn=83ea835a02c7141d51a491cd785844d4)
了解详细分析。

### 问题 2：CPU 权重计算变化

runc 1.3.2+ 和 crun 1.23+ 中新的 cpu.weight 计算可能会影响容器之间的相对 CPU 分配。
升级后请彻底测试您的工作负载。

### 问题 3：Systemd Slice 命名

cgroup v2 使用 systemd slice 命名（例如 `kubepods.slice`），而不是传统的基于路径的
命名。监控工具可能需要更新。

## 资源和参考

### 官方文档

- [内核 cgroup v2 文档](https://www.kernel.org/doc/Documentation/cgroup-v2.txt)
- [内核 cgroup v1 内存文档](https://www.kernel.org/doc/Documentation/cgroup-v1/memory.txt)
- [Kubernetes cgroup v2 指南](https://kubernetes.io/docs/concepts/architecture/cgroups/)
- [Kubernetes cgroup v2 GA 博客](https://kubernetes.io/zh-cn/blog/2022/08/31/cgroupv2-ga-1-25/)

### KEP 和 Issues

- [KEP-5573: 移除 cgroup v1 支持](https://kep.k8s.io/5573)
- [containerd cgroup v1 废弃](https://github.com/containerd/containerd/issues/12443)
- [moby cgroup v1 废弃](https://github.com/moby/moby/issues/51111)
- [cpu.weight 博客](https://github.com/kubernetes/website/pull/52793)
- [cpu.weight 问题](https://github.com/kubernetes/kubernetes/issues/131216)

### 会议演讲

- [KubeCon NA 2022: Cgroups V2: Before You Jump In - Adobe](https://www.youtube.com/watch?v=WxZK-UXKvXk)
- [KubeCon NA 2022: Cgroupv2 Is Coming Soon To a Cluster Near You - Google & RedHat](https://www.youtube.com/watch?v=sgyFCp1CRhA)
- [KubeCon 2020: Kubernetes On Cgroup v2 - Giuseppe Scrivano, Red Hat](https://www.youtube.com/watch?v=u8h0e84HxcE)

### 社区资源

- [OCI Runtime Spec cgroup v2 支持 (PR #1040)](https://github.com/opencontainers/runtime-spec/pull/1040)
- [容器核心技术：cgroups](https://www.rectcircle.cn/posts/container-core-tech-9-cgroup/)
- [Linux cgroups 介绍](https://www.cnblogs.com/Linux-tech/p/12961296.html)

## 结论

从 cgroup v1 迁移到 cgroup v2 是容器生态系统的重要进步。cgroup v2 的统一层级、改进的
资源控制器以及 PSI 等功能为容器化工作负载提供了更好的资源管理和可观测性。

关键要点：

1. **现在就开始规划**：cgroup v1 在 Kubernetes 1.35 中已废弃
2. **检查您的 Linux 发行版**：确保它支持 cgroup v2
3. **升级运行时依赖**：使用 runc 1.3.2+ 或 crun 1.23+
4. **彻底测试**：验证您的工作负载在 cgroup v2 下正常工作
5. **监控升级过程**：在 kubeadm 升级期间注意警告信息

容器资源管理的未来是 cgroup v2。拥抱这一变化，享受更一致、更高效、功能更丰富的 cgroup
接口带来的好处！

---

**作者**：AI 基础设施学习路径
**日期**：2025 年 11 月 26 日
**标签**：#kubernetes #cgroup #linux #container-runtime #migration
