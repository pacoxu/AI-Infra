---
status: Active
maintainer: pacoxu
date: 2026-09-17
last_updated: 2026-09-17
tags: containerd, cri, nri, erofs, snapshotter, kubernetes, runtime, release-notes
canonical_path: docs/blog/2026-09-17/2026-09-17-containerd-2.4-lts-cleanup-window_zh.md
source_urls:
  - https://github.com/containerd/containerd/releases/tag/v2.4.0
  - https://github.com/containerd/containerd/blob/main/RELEASES.md
---

# containerd v2.4.0

> 原文：[containerd v2.4.0](https://github.com/containerd/containerd/releases/tag/v2.4.0)
>
> 发布日期：2026 年 9 月 16 日

欢迎使用 containerd v2.4.0！

containerd 2.4 是常规（非 LTS）版本，支持窗口更短，面向希望更早使用新功能的用户。作为 2.3 LTS 之后的版本，它处于发布周期中可以移除先前已废弃功能的节点，因此可能包含破坏性变更；升级前请阅读下方说明，并先清除当前版本中的 deprecation warning。

优先考虑稳定性和更长支持周期的用户，应继续使用 2.3 LTS。

containerd 2.3 是当前 LTS，发布于 2026-04-30，支持到 2028-04-30。从 2.3 起次版本大约每 4 个月发布一次，常规版本支持约 8 个月，每年指定一个 LTS。2.4 就是这个常规版本；需要更长支持窗口时继续留在 2.3。

## Highlights

### Container Runtime Interface (CRI)

- 为 CRI 中的 image mounts 启用 mount manager（[#13542](https://github.com/containerd/containerd/pull/13542)）
- 在 CRI plugin info 中导出 sandbox image 和 CNI 目录配置（[#13940](https://github.com/containerd/containerd/pull/13940)）
- 将 `runtimeFeatures.UserNamespacesHostNetwork` 默认值设为 `true`（[#13162](https://github.com/containerd/containerd/pull/13162)）
- 支持对非 runc runtime 做 OCI runtime feature introspection（[#13504](https://github.com/containerd/containerd/pull/13504)）

### Image Distribution

- 拉取 descriptor URL 时去掉敏感认证头（[#12889](https://github.com/containerd/containerd/pull/12889)）
- 支持把 registry 的 HTTP 299 warning header 传到 resolver（[#12698](https://github.com/containerd/containerd/pull/12698)）
- gzip layer 解压改用 klauspost/compress（[#13560](https://github.com/containerd/containerd/pull/13560)）

### Image Storage

- 增加 client option：即使 snapshot 已存在，unpack 时仍可拉取全部 layer content（[#14126](https://github.com/containerd/containerd/pull/14126)）
- content create event 中带上 media type（[#13833](https://github.com/containerd/containerd/pull/13833)）
- 为 GC collection context 增加 forward References（[#13634](https://github.com/containerd/containerd/pull/13634)）

### Node Resource Interface (NRI)

- 向 NRI plugin 暴露 container 的 image name、digest 和 config digest（[#13960](https://github.com/containerd/containerd/pull/13960)）
- 对仍使用已废弃 NRI 接口的 plugin 发出 deprecation warning（[#13916](https://github.com/containerd/containerd/pull/13916)）

### Runtime

- 默认 mask Linux 容器中的 `/proc/interrupts` 以及 CPU thermal throttle sysfs 路径（[#14090](https://github.com/containerd/containerd/pull/14090)）
- 增加 `UpdateSandbox` RPC，把 sandbox controller 的更新传到 shim（[#14105](https://github.com/containerd/containerd/pull/14105)）
- 容器被显式 stop 后，`restart=always` 不会立刻再拉起（[#13993](https://github.com/containerd/containerd/pull/13993)）
- 把 tracing context 从 shim 传到 runc 和 hooks（[#14036](https://github.com/containerd/containerd/pull/14036)）
- 修复容器 rootfs 里 `/etc/passwd` 或 `/etc/group` 为 symlink 时的 user/group 查找失败（[#13818](https://github.com/containerd/containerd/pull/13818)）
- 在 `pkg/shim` 中实现 Windows named-pipe server 和 log streaming（[#13948](https://github.com/containerd/containerd/pull/13948)）
- Windows 上默认启用 log scrubbing（[#13837](https://github.com/containerd/containerd/pull/13837)）
- checkpoint 时允许指定 runc 的 parent checkpoint 目录（[#13699](https://github.com/containerd/containerd/pull/13699)）

### Snapshotters

- 为 EROFS snapshotter 的 layer content cache 增加 Prometheus metrics（[#13941](https://github.com/containerd/containerd/pull/13941)）
- EROFS snapshotter 支持 warm image cache（[#13813](https://github.com/containerd/containerd/pull/13813)）
- 为 snapshot 增加 max size label（[#13520](https://github.com/containerd/containerd/pull/13520)）

### Breaking

移除已废弃的 CRI 和 tracing 配置项（[#14166](https://github.com/containerd/containerd/pull/14166)）：

- 移除 CRI runtime 配置中的 `enable_cdi`（CDI 现在始终启用）
- 移除 CRI CNI 配置中的 `bin_dir`（改用 `bin_dirs`）
- 移除 OTLP tracing processor 配置中的 `endpoint`、`protocol` 和 `insecure`（改用标准 OTLP 环境变量）
- 移除 internal tracing 配置中的 `service_name` 和 `sampling_ratio`（改用标准 OpenTelemetry 环境变量）

另外：

- 移除 `CreateContainer` 中的 restore（[#13871](https://github.com/containerd/containerd/pull/13871)）

### Deprecations

- 废弃 shim annotation `containerd.io/runtime-allow-mounts`，改用 `MountCapabilities` bootstrap extension（[#14002](https://github.com/containerd/containerd/pull/14002)）
- 从 pkg 中移除已废弃的 `shim.Command`（[#13991](https://github.com/containerd/containerd/pull/13991)）
- 废弃 runc options 中的 task API address 和 version 字段，迁到 `CreateTaskRequest`（[#13360](https://github.com/containerd/containerd/pull/13360)）

请试用本次发布的二进制，并在
[containerd/containerd issues](https://github.com/containerd/containerd/issues)
反馈问题。上一版是 [v2.3.0](https://github.com/containerd/containerd/releases/tag/v2.3.0)。

## Contributors

本次发布包含 658 个 commit。贡献者名单如下（按官方 Release Notes 顺序）：

- Maksym Pavlenko
- Sebastiaan van Stijn
- Samuel Karp
- Derek McGowan
- Wei Fu
- Akihiro Suda
- Mike Brown
- Paweł Gronowski
- Chris Henzie
- Phil Estes
- Brian Goff
- Austin Vazquez
- ningmingxiao
- Jordan Liggitt
- Akhil Mohan
- Eshaan Mathur
- Krisztian Litkey
- Chris Ayoub
- Kazuyoshi Kato
- Kir Kolyshkin
- Sergey Kanzhelev
- Ahmet Alp Balkan
- Arpit Jain
- Cindy Li
- Damien Grisonnet
- Esteban Ginez
- Gao Xiang
- Harsh Rawat
- Laura Lorenz
- Maksim An
- Oleh Konko
- Philip Laine
- Abhishek Bhunia
- Alan Grosskurth
- Albin Kerouanton
- Alex Lyn
- Aman Raj
- Amir Alavi
- Amit Barve
- Andrew Halaney
- AprilNEA
- Arjun Yogidas
- Ayato Tokubi
- Aysha Afrah Ziya
- Ben Cressey
- Bing Hongtao
- Chris Crone
- Craig Gumbley
- Daniel De Graaf
- Davanum Srinivas
- Dr. Jan-Philip Gehrcke
- Harshal Patel
- Henry Wang
- Hsiu-Chi Tsai
- JP Phillips
- Jing Chen
- Kohei Tokunaga
- LEI WANG
- Martín Fernández
- Mikhail Dmitrichenko
- Nahum Litvin
- Nikolaus Schuetz
- Pablo Garcia Caceres
- Paco Xu
- Robert Cronin
- SaloniRathi
- Shambhavi Srivastava
- Tianon Gravi
- XlabAI
- Yuanliang Zhang
- ayush-panta
- crawfordxx
- cshung
- match man
- s3onghyun
- 归寂
- 徐晓伟

## 该下载哪个文件

- `containerd-<VERSION>-<OS>-<ARCH>.tar.gz`：推荐。动态链接 glibc 2.35（Ubuntu 22.04）。
- `containerd-static-<VERSION>-<OS>-<ARCH>.tar.gz`：静态链接。给不用 glibc >= 2.35 的 Linux 发行版。不是 position-independent。

除了 containerd，通常还需要从官方站点安装 runc 和 CNI plugins。

参见 [Getting Started](https://github.com/containerd/containerd/blob/main/docs/getting-started.md)。

## 参考

- containerd Official Release:
  [v2.4.0](https://github.com/containerd/containerd/releases/tag/v2.4.0)
- [Versioning and Release (`RELEASES.md`)](https://github.com/containerd/containerd/blob/main/RELEASES.md)
