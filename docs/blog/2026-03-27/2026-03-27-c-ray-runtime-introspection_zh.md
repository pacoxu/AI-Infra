---
status: Active
maintainer: pacoxu
date: 2026-03-27
tags: c-ray, containerd, cri-o, runtime, tui, kubernetes, observability
canonical_path: docs/blog/2026-03-27/2026-03-27-c-ray-runtime-introspection_zh.md
source_urls:
  - https://github.com/Iceber/c-ray
  - https://github.com/Iceber/c-ray/blob/main/README.md
---

# c-ray 代码梳理：一个面向容器运行时层的 TUI 观察器

如果只看一句话，`c-ray` 的定位是：**在节点上直接面向 container runtime 做深度排障和状态观察**。

它不是 Kubernetes 控制面工具，也不是应用发布平台，而是把焦点放在容器真正运行时的数据上，包括：

- 容器/POD/镜像关系；
- 进程树与资源占用；
- 挂载来源与状态；
- CNI 网络与 CRI 元数据；
- 镜像层、快照和可写层信息。

## 先说结论

从代码实现看，`c-ray` 有三个值得关注的工程点：

1. **统一 Runtime 抽象**：同一套接口同时支持 `containerd` 和 `CRI-O`。
2. **“对象句柄”而非“平面 API”**：先拿 `Container/Image/Pod` 句柄，再按需拉取详情，便于缓存和懒加载。
3. **运行时数据融合能力强**：把 CRI 声明、OCI spec、进程 live 数据做统一合并，尤其是挂载视图可读性很好。

## 代码结构速览

核心目录如下：

- `cmd/cray`：程序入口，TUI + CLI（`cray test ...`）；
- `pkg/runtime`：运行时抽象层 + `containerd`/`crio` 实现；
- `pkg/sysinfo`：基于 procfs/cgroup/mountinfo 的系统采集；
- `pkg/ui`：基于 `tview/tcell` 的终端交互界面；
- `docs/`：实现说明与设计文档。

## 架构拆解

### 1) 运行时抽象：先拿句柄，再查详情

`pkg/runtime/interface.go` 没有把接口设计成“大而全的查询函数集合”，而是：

- `ListContainers/GetContainer` 返回 `Container` 句柄；
- 后续通过 `Container.Info/Config/State/Network/Mounts/Processes/...` 分域查询。

这个设计直接带来两个好处：

- 可以把不常变的信息（如 OCI spec、CRI status）缓存到句柄内部；
- UI 可以按页签懒加载，不需要一次性抓全量数据。

### 2) 双 runtime 适配：containerd 与 CRI-O 共存

`cmd/cray/test.go` 里有 socket 推断逻辑：根据路径关键词和常见 unix socket 自动识别 runtime 类型，然后实例化：

- `pkg/runtime/containerd`
- `pkg/runtime/crio`

二者都实现同一套 `runtime.Runtime` 接口，因此 UI 层不需要关心底层差异。

### 3) 挂载信息合并是亮点

`pkg/runtime/cri/mounts.go` 对挂载做了四阶段合并：

1. CRI config mounts；
2. CRI status-only mounts；
3. OCI spec 里剩余的 runtime default mounts；
4. 未匹配的 live mounts（来自 `/proc/<pid>/mountinfo`）。

最后还会打上 `Origin/State/Note`，例如：

- 来源是 `cri`、`runtime-default` 还是 `live-extra`；
- 状态是 `declared+live`、`declared-only` 还是 `live-only`。

这对定位“声明与实际挂载不一致”的问题很有价值。

### 4) sysinfo 采集链路：以 `/proc` 为中心

`pkg/sysinfo` 这层做了比较扎实的基础设施：

- `ProcReader`：读取进程 stat/cmdline/status/io；
- `ProcessCollector`：进入容器视角收集进程树；
- `Sampler`：基于两次采样计算 CPU%、IO 速率、网络速率；
- `CGroupReader`：读取 cgroup v1/v2 资源限制。

这让 TUI 能看到“结构化进程关系 + 动态资源趋势”，不只是静态表格。

### 5) TUI 组织：主视图 + 容器详情工作区

`pkg/ui` 的结构比较清晰：

- Main 页面：Containers / Images / Pods 三个主 tab；
- Detail 页面：Summary / Processes / Filesystem / Runtime / Network 五个工作区；
- `MainView` 定时刷新，`ContainerDetailView` 按活跃 tab 刷新，降低无效查询。

整体交互策略是“先全局浏览，再下钻定位”，和故障排查流程一致。

## 适合什么场景

`c-ray` 目前最适合以下场景：

- Kubernetes 节点问题排查（尤其是 container runtime 层）；
- 挂载、镜像层、可写层异常定位；
- 容器进程/资源行为分析；
- 需要在 SSH 终端内快速观察 runtime 细节的运维/SRE 场景。

## 当前状态与一个注意点

按我本地拉取的 `main`（最新提交时间 **2026-03-17**）进行快速验证时，`go test ./...` 在 `cmd/cray` 目录构建失败，原因是 `test.go` 与 `v1test.go` 存在重复符号定义。

这说明项目仍在快速重构期，但核心架构方向已经比较清楚，尤其是“统一 runtime 接口 + 多数据源融合”的思路值得持续跟进。

## 总结

`c-ray` 的价值不在“又一个容器列表工具”，而在它把运行时细节做成了可交互、可追踪、可解释的诊断界面。

对于做 AI-Infra / Kubernetes 平台工程的人来说，它是一个很实用的节点侧观察器，也是一套值得参考的 runtime introspection 代码骨架。
