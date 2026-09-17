---
status: Active
maintainer: pacoxu
date: 2026-09-17
last_updated: 2026-09-17
tags: containerd, cri, nri, erofs, snapshotter, kubernetes, runtime, ai-infrastructure, release-notes
canonical_path: docs/blog/2026-09-17/2026-09-17-containerd-2.4-lts-cleanup-window_zh.md
source_urls:
  - https://github.com/containerd/containerd/releases/tag/v2.4.0
  - https://github.com/containerd/containerd/blob/main/RELEASES.md
  - https://containerd.io/releases/
  - https://github.com/containerd/containerd/pull/14166
  - https://github.com/containerd/containerd/pull/13813
  - https://github.com/containerd/containerd/pull/13542
  - https://github.com/containerd/containerd/pull/13960
  - https://github.com/kubernetes/enhancements/issues/5823
---

# containerd 2.4：LTS 之后的清理窗口，升级前先消掉废弃警告

containerd [`v2.4.0`](https://github.com/containerd/containerd/releases/tag/v2.4.0)
于 **2026-09-16** 发布，共 658 个提交。站在节点运行时和 AI 基础设施团队的视角，
这版真正要先读懂的不是功能清单，而是它在发布周期里的位置：

**2.4 是接在 2.3 LTS 后面的常规（non-LTS）短周期版本。** 官方明确说：想要稳定和
更长支持窗口，继续停在 2.3；2.4 面向想更早拿到新功能的用户，也是废弃项被真正删掉
的窗口。

## 先说结论

1. **不要把 2.4 当成“下一个 LTS”。** 2.3 才是当前 LTS（2026-04-30 到
   2028-04-30）。常规次版本大约支持 8 个月；`RELEASES.md` 里 2.4 的 EOL 仍标成
   2027-04-26（tentative）。
2. **升级前必须先消掉当前版本的 deprecation warning。** containerd 规定：功能只能
   在 LTS **之后紧接着的那个版本** 删除。2.4 正好落在这个位置。
3. **配置层面已经发生 breaking。** `enable_cdi`、`bin_dir`、OTLP/tracing 若干字段、
   CRI `CreateContainer` restore 都删了。registry 的 `auths` / `configs` /
   `mirrors` 原计划也在 2.4 移除，实际推迟到 2.7。
4. **对 AI-Infra 有用的增量** 主要在四条线上：EROFS 热缓存、NRI 拿到镜像
   name/digest、CRI 镜像挂载走 mount manager、CDI 变为常开。

## 1. 先看发布策略，再看功能清单

从 2.3 起，containerd 按 **4 个月** 发一个次版本，对齐 Kubernetes 的 4 月 / 8 月 /
12 月节奏。每年一个 LTS，其余是常规版本：

| 版本 | 类型 | 发布 | 支持到 |
| --- | --- | --- | --- |
| 2.3 | LTS | 2026-04-30 | 2028-04-30 |
| 2.4 | 常规 | 2026-09-16 | 约 8 个月（表上暂记 2027-04-26） |

升级路径也值得单独记：相邻次版本可以升（2.3 → 2.4），LTS 之间也可以直跳（例如
1.7 → 2.3），但不能跨一个常规次版本硬跳（2.3 → 2.5 不行）。

谁该跟 2.4：

- 要吃 EROFS / NRI / CRI 新路径，且能接受 8 个月支持窗口的平台团队；
- 正在跟 Kubernetes 1.37 做 runtime 联调，希望用同一代 containerd 做 e2e 的团队。

谁该停在 2.3：

- 生产节点以稳定和长支持为主，不急着清废弃配置；
- 发行版 / 托管 Kubernetes 还没把 2.4 编进默认 runtime。

## 2. 配置清理：2.4 真正删了什么

[#14166](https://github.com/containerd/containerd/pull/14166) 把一批早先标废弃的
配置项从 2.4 里拿掉。升级 checklist 可以按这张表对：

| 位置 | 删除项 | 替代 |
| --- | --- | --- |
| CRI runtime | `enable_cdi` | CDI **始终开启**，没有关闭开关 |
| CRI CNI | `bin_dir` | 改用 `bin_dirs`（目录列表） |
| OTLP tracing processor | `endpoint` / `protocol` / `insecure` | `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`、`OTEL_EXPORTER_OTLP_PROTOCOL`、`OTEL_SDK_DISABLED` |
| internal tracing | `service_name` / `sampling_ratio` | `OTEL_SERVICE_NAME`、`OTEL_TRACES_SAMPLER*` |
| CRI `CreateContainer` | restore 路径 | 后续走 [KEP-5823](https://github.com/kubernetes/enhancements/issues/5823) 的 `RestorePod` |

CRI registry 段的 `auths` / `configs` / `mirrors` 在 `RELEASES.md` 里曾把移除目标
写成 2.4。2.4.0 实际把这项推迟到 **2.7**，2.4 里仍可过渡，但不应再新增依赖。

另外还有一组 deprecation，2.4 还没删，但已经不能当长期接口：

- shim 注解 `containerd.io/runtime-allow-mounts` 废弃，改走
  `MountCapabilities` bootstrap extension
  （[#14002](https://github.com/containerd/containerd/pull/14002)）；
- runc options 里的 task API address / version 废弃，迁到 `CreateTaskRequest`
  （[#13360](https://github.com/containerd/containerd/pull/13360)）；
- `pkg` 里的 `shim.Command` 已移除
  （[#13991](https://github.com/containerd/containerd/pull/13991)）。

旧 NRI 插件会开始打 deprecation warning
（[#13916](https://github.com/containerd/containerd/pull/13916)）。GPU 共享、
拓扑、精细化 cgroup 这类插件如果还停在旧接口，2.4 是迁 API 的窗口，不是可以
继续拖的信号。仓库里对 NRI 的背景见
[Node Resource Interface](../../kubernetes/nri.md)。

## 3. 对 AI-Infra 有用的增量

### 3.1 EROFS：热缓存从“能用”往“可运营”走

EROFS snapshotter 是 2.4 里最接近镜像冷启动和模型分发的一条线：

- 支持 warm image cache，可从预转换的 layer content cache 取层
  （[#13813](https://github.com/containerd/containerd/pull/13813)）；
- layer content cache 补了 Prometheus 指标
  （[#13941](https://github.com/containerd/containerd/pull/13941)）；
- snapshot 可打 max size label
  （[#13520](https://github.com/containerd/containerd/pull/13520)）；
- 并行 unpack、多 cache 目录、dm-verity 和 fsview fallback 也在同一窗口里补齐。

如果节点已经在评估 EROFS / tar index 来降镜像展开成本，2.4 的意义是：缓存不再
只是“转换一次”，而是有预热路径和可观测性。它解决的是 **层转换和本地命中**，
不是跨节点的模型分发；后者仍要和 Harbor / Dragonfly / ModelExpress 这类栈分开看。

### 3.2 NRI：插件能看见镜像名和 digest

[#13960](https://github.com/containerd/containerd/pull/13960) 把解析后的镜像
name、digest、config digest 写进 container metadata，NRI 插件可以直接读。

这对节点侧资源插件很具体：按镜像身份做 GPU 绑定、NUMA、精细化 cgroup 或安全策略
时，不必再自己倒推 CRI 镜像引用。配合上一节的旧接口 warning，2.4 适合做一次
“新字段用起来、旧 API 迁走”的插件回归。

### 3.3 CRI：镜像挂载、UserNS 默认值、非 runc introspection

- 镜像挂载启用 mount manager
  （[#13542](https://github.com/containerd/containerd/pull/13542)），挂载失败时
  才 unmount，避免误伤已有 volume；
- `runtimeFeatures.UserNamespacesHostNetwork` 默认改为 `true`
  （[#13162](https://github.com/containerd/containerd/pull/13162)）；
- 非 runc 的 OCI runtime 也能做 feature introspection
  （[#13504](https://github.com/containerd/containerd/pull/13504)）；
- CRI plugin info 导出 sandbox 镜像和 CNI 目录配置
  （[#13940](https://github.com/containerd/containerd/pull/13940)）。

镜像 volume、Kata / crun / 其他 shim、以及 user namespace + hostNetwork 的组合，
都应该在灰度节点上复测一遍。默认值变化不会写进 breaking 列表，但行为会变。

### 3.4 CDI 常开，以及运行时安全默认值

`enable_cdi` 删除意味着 **GPU / 设备注入不能再靠关 CDI 做兼容回退**。设备插件、
CDI spec、NRI 注入三条路径要在 2.4 节点上同时跑通。

运行时侧还有几处默认收紧和排障修复：

- 默认 mask `/proc/interrupts` 和 CPU thermal throttle sysfs
  （[#14090](https://github.com/containerd/containerd/pull/14090)）；
- 新增 `UpdateSandbox` RPC，sandbox controller 更新能传到 shim
  （[#14105](https://github.com/containerd/containerd/pull/14105)）；
- tracing context 从 shim 传到 runc 和 hooks
  （[#14036](https://github.com/containerd/containerd/pull/14036)）；
- rootfs 里 `/etc/passwd`、`/etc/group` 是 symlink 时的用户查找失败已修
  （[#13818](https://github.com/containerd/containerd/pull/13818)）；
- `restart=always` 在显式 stop 后不会立刻再拉起
  （[#13993](https://github.com/containerd/containerd/pull/13993)）。

最后一条主要影响直接用 containerd（而不是纯 CRI）的客户端。Kubernetes 工作负载
通常不走这条 restart policy，但混合节点上的非 K8s 容器要回归。

### 3.5 镜像分发与存储

- 拉 descriptor URL 时剥掉敏感认证头
  （[#12889](https://github.com/containerd/containerd/pull/12889)）；
- registry 的 HTTP 299 warning 会传到 resolver
  （[#12698](https://github.com/containerd/containerd/pull/12698)）；
- gzip 解压改用 `klauspost/compress`
  （[#13560](https://github.com/containerd/containerd/pull/13560)）；
- unpack 时可选择即使 snapshot 已存在也把 layer content 拉全
  （[#14126](https://github.com/containerd/containerd/pull/14126)）。

私有 registry、镜像加速和“层已经在 snapshot 里但仍要校内容”的场景，这几条比
单纯看吞吐更重要。299 warning 尤其值得接到镜像拉取日志里，避免 registry 侧的
弃用提示被运行时吞掉。

## 4. 依赖、平台和二进制

2.4.0 自带的关键版本：

| 组件 | 版本 |
| --- | --- |
| containerd API | v1.12.0 |
| Kubernetes / CRI 测试依赖 | v1.37.0 |
| NRI | v0.12.3 |
| runc | v1.5.1 |
| crun | v1.29.1 |
| Go | 1.26.8 / 1.27.1 |

另外新增 **loong64** 构建；Windows 默认开启 log scrubbing，shim 补了 named pipe
和日志流。官方 Kubernetes 兼容矩阵（`RELEASES.md`）在 2.4.0 发布当天仍写到
1.36 / containerd 2.3，1.37 的推荐 runtime 行以该表后续更新为准。

下载优先用动态链接包 `containerd-2.4.0-linux-*.tar.gz`（glibc ≥ 2.35）。静态包
只给没有新 glibc 的发行版，且不是 PIE。runc 和 CNI 插件仍要单独装。

## 5. 升级清单（建议）

1. 在 **2.3** 上把 deprecation warning 清零，再考虑升 2.4。日志里还在报的配置，
   2.4 里多半已经不存在。
2. 配置迁移按项改：`bin_dir` → `bin_dirs`；删掉 `enable_cdi`；tracing 改走
   OTel 环境变量，不要再写 `endpoint` / `service_name`。
3. 确认节点 **不再依赖 CRI `CreateContainer` restore**。Checkpoint 恢复要跟
   KEP-5823 的时间线对齐，不能假设 2.4 还留后路。
4. GPU / 设备节点做一次 CDI + NRI 回归：CDI 关不掉了，旧 NRI 插件会告警。
5. 若使用镜像 volume 或非 runc runtime（crun / Kata / 其他 shim），复测镜像挂载
   和 OCI feature introspection。
6. 评估 `UserNamespacesHostNetwork=true` 对现网 user namespace Pod 的影响。
7. 已经在试点 EROFS 的节点，打开 layer cache 指标，并单独测 warm cache 命中，
   不要和 registry 拉取吞吐混在一张图里。
8. 镜像拉取链路打开 299 warning 和认证头剥离后的私有仓库回归，尤其是带
   `desc.urls` 的镜像。
9. 生产集群若以支持周期为先，**继续停在 2.3 LTS**；2.4 适合预发、新集群和
   明确要吃新 snapshotter / NRI 字段的节点池。

## 总结

containerd 2.4 的主线不是“更快的一次发布”，而是 **LTS 之后把废弃项真正拆掉**。
功能增量集中在 EROFS 可运营化、NRI 镜像身份、CRI 镜像挂载和 CDI 常开；这些对
AI 节点有用，但都建立在“你已经不依赖旧配置”的前提上。

平台团队可以把 2.4 当成一次 **配置体检 + 小范围灰度**：先在 2.3 消掉警告，再
决定要不要跟。要稳定，就留在 2.3。

## 参考

- containerd Official Release:
  [v2.4.0](https://github.com/containerd/containerd/releases/tag/v2.4.0)
- [Versioning and Release (`RELEASES.md`)](https://github.com/containerd/containerd/blob/main/RELEASES.md)
- [containerd.io/releases](https://containerd.io/releases/)
- Deprecations and removals:
  [containerd/containerd#14166](https://github.com/containerd/containerd/pull/14166)
- [KEP-5823 RestorePod](https://github.com/kubernetes/enhancements/issues/5823)
- 本仓库：[NRI](../../kubernetes/nri.md)
