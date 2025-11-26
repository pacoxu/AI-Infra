---
status: Active
maintainer: pacoxu
date: 2025-11-26
tags: kubernetes, cgroup, linux, container-runtime, migration
canonical_path: docs/blog/2025-11-26/cgroup-v2.md
---

# Migrating to cgroup v2: What Kubernetes Users Need to Know

## Introduction

With the release of Kubernetes 1.35, cgroup v1 has been officially deprecated.
This marks a significant milestone in the Kubernetes ecosystem's transition
to the more modern and efficient cgroup v2 interface. In this blog post, we'll
explore what cgroup v2 brings to the table, why the migration is happening,
and what you need to do to prepare.

### Key Announcements

- **Kubernetes 1.31**: cgroup v1 support moved to
  [maintenance mode](https://kubernetes.io/blog/2024/08/14/kubernetes-1-31-moving-cgroup-v1-support-maintenance-mode/)
- **Kubernetes 1.35**: cgroup v1 is
  [officially deprecated](https://github.com/kubernetes/enhancements/issues/5573).
  Removal will follow the Kubernetes deprecation policy
- **Container Runtimes**: Both
  [containerd](https://github.com/containerd/containerd/issues/12443) and
  [moby (Docker)](https://github.com/moby/moby/issues/51111) are also
  deprecating cgroup v1 support

## What Are cgroups?

Control groups (cgroups) are a Linux kernel feature that allows you to
allocate resources—such as CPU time, system memory, network bandwidth, or
combinations of these resources—among user-defined groups of tasks (processes)
running on a system.

### cgroup v1: The Original Design

cgroup v1 was developed at Google and merged into Linux kernel 2.6.24 in
January 2008. It introduced resource controllers (subsystems) that were added
incrementally:

| Kernel Version | Year | Controllers Added |
|----------------|------|-------------------|
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

### Issues with cgroup v1

Despite its success, cgroup v1 had several well-known limitations:

1. **Separate Controller Hierarchies**: Each controller must be handled
   separately. The flexibility of having different hierarchies is not used
   in practice
2. **Memory Subsystem Integration**: Integration with some kernel subsystems,
   like memory, is not ideal
3. **Unsafe Delegation**: Delegation of a subtree to a less privileged process
   is not safe
4. **No Resource Reservation**: No mechanism for resource allocation
   guarantees
5. **Inconsistent Interfaces**: Inconsistencies among the different subsystems
6. **Non-Atomic Operations**: Creating, deleting, or moving cgroups must be
   done for each controller
7. **OOM Killer Issues**: The OOM killer is not cgroup-aware; processes from
   different containers/cgroups can be killed at the same time

### cgroup v2: The Unified Hierarchy

cgroup v2 was officially released with Linux kernel 4.5 in March 2016. It
introduced a unified hierarchy that addresses many of the v1 limitations:

| Kernel Version | Year | Controllers Added |
|----------------|------|-------------------|
| 4.5 | 2016 | io, memory, pids |
| 4.11 | 2017 | perf_event, rdma |
| 4.15 | 2018 | cpu |
| 5.0 | 2019 | cpuset |
| 5.2 | 2019 | freezer |
| 5.6 | 2020 | hugetlb |

## cgroup v1 vs v2 Hierarchy Comparison

### v1: Multiple Hierarchies

In cgroup v1, each controller has its own hierarchy:

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

### v2: Unified Hierarchy

In cgroup v2, all controllers share a single hierarchy:

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

## Key Improvements in cgroup v2

### 1. Unified Hierarchy

All resource controllers are organized in a single tree, simplifying
management and eliminating inconsistencies between different controller
hierarchies.

### 2. Improved CPU Controller

The CPU controller in cgroup v2 uses `cpu.weight` (range 1-10000, default 100)
instead of `cpu.shares` (range 2-262144, default 1024):

```text
# cgroup v1
cpu.shares = 1024  (relative weight)
cpu.cfs_quota_us = 100000  (hard limit)
cpu.cfs_period_us = 100000  (period)

# cgroup v2
cpu.weight = 100  (relative weight, more intuitive scale)
cpu.max = "100000 100000"  (quota period format)
```

### 3. Enhanced Memory Controller

cgroup v2 introduces a graduated memory control model:

- **memory.min**: Hard memory protection. Memory below this threshold is never
  reclaimed, even under heavy memory pressure
- **memory.low**: Soft memory protection. Memory below this threshold is
  protected from reclamation if there's reclaimable memory available elsewhere
- **memory.high**: Memory throttling threshold. When memory exceeds this limit,
  the kernel aggressively reclaims memory. This acts as a soft limit
- **memory.max**: Hard memory limit. If memory usage reaches this limit, the
  OOM killer is triggered

This graduated approach provides much finer control over memory management
compared to v1's simple hard limit.

### 4. Pressure Stall Information (PSI)

One of the most significant additions in cgroup v2 is Pressure Stall
Information (PSI), which provides metrics on resource contention:

```bash
# Check CPU pressure
cat /sys/fs/cgroup/kubepods.slice/cpu.pressure
# Output: some avg10=0.00 avg60=0.00 avg300=0.00 total=0
#         full avg10=0.00 avg60=0.00 avg300=0.00 total=0

# Check memory pressure
cat /sys/fs/cgroup/kubepods.slice/memory.pressure
# Output: some avg10=0.00 avg60=0.00 avg300=0.00 total=0
#         full avg10=0.00 avg60=0.00 avg300=0.00 total=0

# Check I/O pressure
cat /sys/fs/cgroup/kubepods.slice/io.pressure
# Output: some avg10=0.00 avg60=0.00 avg300=0.00 total=0
#         full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

PSI metrics include:

- **some**: Percentage of time at least one task is stalled on the resource
- **full**: Percentage of time all tasks are stalled on the resource
- **avg10/avg60/avg300**: Averages over 10s, 60s, and 300s windows

### 5. Safe Delegation

cgroup v2 introduces proper delegation support through:

- `cgroup.subtree_control`: Controls which controllers are enabled in child
  cgroups
- Proper permissions model for unprivileged cgroup management
- Secure delegation to containers and rootless runtimes

### 6. Atomic Operations

In cgroup v2, creating a cgroup automatically enables all controllers,
eliminating the need for separate operations per controller.

## Kubernetes and cgroup v2 Timeline

- **Kubernetes 1.19**: First release with cgroup v2 support
- **Kubernetes Enhancement Proposal (PR #1370)**: Accepted in February 2020
- **Kubernetes 1.25**: cgroup v2 support became stable (GA)
- **Kubernetes 1.31**: cgroup v1 support moved to maintenance mode
- **Kubernetes 1.35**: cgroup v1 officially deprecated

## Migration Guide

### Step 1: Check Your Current cgroup Version

```bash
# Check which cgroup version is mounted
mount | grep cgroup

# For cgroup v1, you'll see multiple mounts like:
# cgroup on /sys/fs/cgroup/cpu type cgroup (...)
# cgroup on /sys/fs/cgroup/memory type cgroup (...)

# For cgroup v2, you'll see a single unified mount:
# cgroup2 on /sys/fs/cgroup type cgroup2 (...)

# Or check the file system type
stat -fc %T /sys/fs/cgroup/
# cgroup2fs for v2, tmpfs for v1
```

### Step 2: Verify Linux Distribution Support

Most modern Linux distributions enable cgroup v2 by default:

| Distribution | cgroup v2 Default Since |
|--------------|------------------------|
| Fedora | 31 (2019) |
| Arch Linux | April 2021 |
| openSUSE Tumbleweed | ~2021 |
| Debian | 11 (Bullseye, 2021) |
| Ubuntu | 21.10 (cgroups v2 available since 20.04) |
| RHEL | 9 (2022) |
| Rocky Linux | 9 (2022) |
| AlmaLinux | 9 (2022) |

### Step 3: Upgrade Container Runtime Dependencies

Kubernetes recommends upgrading your container runtime dependencies when
migrating to cgroup v2:

- **runc**: Upgrade to version **1.3.2 or later**
- **crun**: Upgrade to version **1.23 or later**

> **Important**: These versions include the new `cpu.weight` calculation
> formula that the ecosystem is adopting. See the upcoming blog post at
> [kubernetes/website#52793](https://github.com/kubernetes/website/pull/52793)
> and issue
> [kubernetes/kubernetes#131216](https://github.com/kubernetes/kubernetes/issues/131216)
> for details.

### Step 4: Enable cgroup v2 (if needed)

If your system doesn't have cgroup v2 enabled, add the following to your
kernel boot parameters:

```text
systemd.unified_cgroup_hierarchy=1
```

For GRUB-based systems:

```bash
# Edit /etc/default/grub
GRUB_CMDLINE_LINUX="systemd.unified_cgroup_hierarchy=1"

# Update GRUB
sudo update-grub  # Debian/Ubuntu
# or
sudo grub2-mkconfig -o /boot/grub2/grub.cfg  # RHEL/CentOS
```

### Step 5: Verify Kubernetes Compatibility

Ensure your Kubernetes components are compatible:

- kubelet must be configured to use cgroup v2
- Container runtime (containerd, CRI-O) must support cgroup v2
- All node components should be updated to compatible versions

## Important Considerations for kubeadm Users

> **⚠️ Warning for kubeadm Upgrade Process**
>
> When upgrading Kubernetes clusters managed by kubeadm, be aware of the
> following upgrade sequence:
>
> 1. **Control plane upgrade first**: During this phase, the kubelet is still
>    running the old version. You will see **warning messages** about cgroup v1,
>    not errors
> 2. **kubelet upgrade second**: This is the critical phase. If you ignored
>    the warnings during the control plane upgrade and your node uses cgroup v1,
>    the kubelet will **fail to start** after the upgrade (unless you've
>    modified the `FailCgroupV1` configuration)
>
> **Action Required**: Do not ignore cgroup v1 warnings during control plane
> upgrades. Ensure your nodes are migrated to cgroup v2 before upgrading the
> kubelet to Kubernetes 1.35 or later.
>
> For more details, see
> [kubernetes/system-validators#58](https://github.com/kubernetes/system-validators/issues/58).

## Checking Container Runtime Support

### containerd

```bash
# Check containerd version and config
containerd --version

# Verify cgroup driver in config
cat /etc/containerd/config.toml | grep -i cgroup
# Should show: SystemdCgroup = true
```

### CRI-O

```bash
# Check CRI-O version
crio --version

# Verify cgroup configuration
cat /etc/crio/crio.conf | grep -i cgroup
```

## Common Issues and Troubleshooting

### Issue 1: Memory Metrics Discrepancy

When migrating from cgroup v1 to v2, you might notice differences in memory
metrics reporting. This is due to changes in how memory accounting works
in cgroup v2.

See the blog post
[揭开K8s适配CgroupV2内存虚高的迷局](https://mp.weixin.qq.com/s?__biz=MzI1MzE0NTI0NQ==&mid=2650492905&idx=1&sn=83ea835a02c7141d51a491cd785844d4)
for detailed analysis.

### Issue 2: CPU Weight Calculation Changes

The new cpu.weight calculation in runc 1.3.2+ and crun 1.23+ may affect
relative CPU allocation between containers. Test your workloads thoroughly
after upgrading.

### Issue 3: Systemd Slice Naming

cgroup v2 uses systemd slice naming (e.g., `kubepods.slice`) instead of the
traditional path-based naming. Monitoring tools may need updates.

## Resources and References

### Official Documentation

- [Kernel cgroup v2 Documentation](https://www.kernel.org/doc/Documentation/cgroup-v2.txt)
- [Kernel cgroup v1 Memory Documentation](https://www.kernel.org/doc/Documentation/cgroup-v1/memory.txt)
- [Kubernetes cgroup v2 Guide](https://kubernetes.io/docs/concepts/architecture/cgroups/)
- [Kubernetes cgroup v2 GA Blog](https://kubernetes.io/zh-cn/blog/2022/08/31/cgroupv2-ga-1-25/)

### KEPs and Issues

- [KEP-5573: Remove cgroup v1 Support](https://kep.k8s.io/5573)
- [containerd cgroup v1 Deprecation](https://github.com/containerd/containerd/issues/12443)
- [moby cgroup v1 Deprecation](https://github.com/moby/moby/issues/51111)
- [cpu.weight Blog](https://github.com/kubernetes/website/pull/52793)
- [cpu.weight Issue](https://github.com/kubernetes/kubernetes/issues/131216)

### Conference Talks

- [KubeCon NA 2022: Cgroups V2: Before You Jump In - Adobe](https://www.youtube.com/watch?v=WxZK-UXKvXk)
- [KubeCon NA 2022: Cgroupv2 Is Coming Soon To a Cluster Near You - Google & RedHat](https://www.youtube.com/watch?v=sgyFCp1CRhA)
- [KubeCon 2020: Kubernetes On Cgroup v2 - Giuseppe Scrivano, Red Hat](https://www.youtube.com/watch?v=u8h0e84HxcE)

### Community Resources

- [OCI Runtime Spec cgroup v2 Support (PR #1040)](https://github.com/opencontainers/runtime-spec/pull/1040)
- [Container Core Technology: cgroups](https://www.rectcircle.cn/posts/container-core-tech-9-cgroup/)
- [Linux cgroups Introduction (Chinese)](https://www.cnblogs.com/Linux-tech/p/12961296.html)

## Conclusion

The migration from cgroup v1 to cgroup v2 is an important step forward for
the container ecosystem. cgroup v2's unified hierarchy, improved resource
controllers, and features like PSI provide better resource management and
observability for containerized workloads.

Key takeaways:

1. **Start planning now**: cgroup v1 is deprecated in Kubernetes 1.35
2. **Check your Linux distribution**: Ensure it supports cgroup v2
3. **Upgrade runtime dependencies**: Use runc 1.3.2+ or crun 1.23+
4. **Test thoroughly**: Verify your workloads work correctly with cgroup v2
5. **Monitor the upgrade**: Pay attention to warnings during kubeadm upgrades

The future of container resource management is cgroup v2. Embrace the change
and enjoy the benefits of a more consistent, efficient, and feature-rich
cgroup interface!

---

**Author**: AI Infrastructure Learning Path
**Date**: November 26, 2025
**Tags**: #kubernetes #cgroup #linux #container-runtime #migration
