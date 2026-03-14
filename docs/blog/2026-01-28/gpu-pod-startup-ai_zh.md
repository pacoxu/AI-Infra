---
status: Active
maintainer: pacoxu
date: 2026-01-28
tags: kubernetes, pod, startup, optimization, gpu, ai, cold-start, dra
canonical_path: docs/blog/2026-01-28/gpu-pod-startup-ai_zh.md
---

# Kubernetes Pod 启动速度优化指南：AI 版

[English Version](./gpu-pod-startup-ai.md)

## 背景与目标：AI Pod 冷启动为什么更难

在通用工作负载里，Pod 启动慢通常被归结为"镜像拉取慢""初始化逻辑重""探针配置不当"。
但当工作负载变成 AI——尤其是 GPU 推理或训练的在线服务——情况就完全不一样了。"Pod
启动完成"往往并不等于"业务可用"。你还要额外经历一系列 AI 特有的初始化环节：GPU
驱动与运行时初始化、模型权重与 tokenizer 等工件的准备、框架首次执行时的编译优化与
内核缓存建立，以及推理服务的 warmup。这些环节叠加在一起，使得 AI Pod 的冷启动远比
普通应用复杂。

更关键的是，AI 冷启动的端到端关键路径经常被"节点侧扩容"主导，而不是 Pod 自身的
创建。当集群没有空闲 GPU 节点时，节点自动扩展需要先拉起新节点；节点就绪后还要等待
加速器 device plugin 把 GPU 资源上报给控制面，期间 Pod 只能 Pending。在一些环境里，
这一段等待可能"按分钟计"。

因此，写 AI 版的启动速度优化，视角不应该是"罗列技巧"，而是"缩短关键路径"——先把
AI Pod 的启动拆成可度量的阶段，再为每个阶段找到最有收益的优化杠杆。

## 定义 AI Pod 的启动时间轴

优化的第一步不是"动手改配置"，而是定义度量口径：你到底在优化哪一段时间？

Kubernetes 把 Pod 生命周期的关键状态与条件都标准化输出了。Phase 和 Conditions 提供
了足够细的里程碑，其中 Pending 阶段就明确包含"等待调度 + 下载镜像"等时间。一个
适合 AI 的"端到端启动时间轴"可以这样定义（从控制面创建 Pod 开始，到业务真正可服务
为止）：

第一步是容量可用——有可用节点，或节点扩容完成。如果没有节点，Pod 会因为不可调度而
等待节点自动扩缩容。第二步是调度完成，对应 Pod 条件 `PodScheduled=True`。第三步是
沙箱与网络就绪，对应 `PodReadyToStartContainers=True`（beta，默认启用），意味着
Pod sandbox 已创建且网络已配置完成。第四步是初始化容器完成，对应 `Initialized=True`。
第五步是容器 ready 与 Pod ready，`ContainersReady=True` 且 `Ready=True`，此时才会
进入 Service 的负载均衡池。

但对 AI Pod 来说，传统的 readinessProbe 判定 Ready 往往不够——模型可能尚未加载完成，
warmup 尚未执行，这时候把实例暴露给流量会导致首请求延迟飙升。Kubernetes 提供了
`readinessGates` 机制：Pod 只有在"所有容器 ready"并且"所有 readinessGates 指定
的自定义条件为 True"时，才会被视为 Ready。

```yaml
spec:
  readinessGates:
  - conditionType: ai.example.com/ModelLoaded
  - conditionType: ai.example.com/WarmupDone
```

这样你就能把 warmup 从"业务流量关键路径"移走，用 readinessGates 保证首请求不踩
冷启动——这才是 AI 版启动优化最应该强调的工程实践。

## 分段定位与可观测性：把"慢"变成可优化的指标

AI Pod 冷启动很容易陷入"感觉很慢"的模糊讨论，最后变成"改了一堆参数也不知道是否
有效"。更稳妥的做法是：先用分段计时把瓶颈固定在某一段，再谈优化手段。Kubernetes
的 Phase、Conditions、事件等信号足够丰富，你需要做的是把它们串成一张时间表。

这里建议定义一套"AI 冷启动分段指标"：

`T_node_wait` 是等待节点扩容与加速器能力就绪的时间。在 GPU 场景，加速器 device
plugin 可能需要数分钟才能把资源上报到集群，导致即便节点已启动，Pod 仍无法调度到
该节点，甚至引发重复扩容。

`T_schedule` 是从 Pod 创建到 `PodScheduled=True`。在拓扑感知、亲和性、多 GPU 等
约束变多时，该段会显著变长。

`T_image` 是镜像与依赖进入节点的时间（含解压）。镜像层越大、并发越高、节点磁盘与
网络越拥塞，该段越可能成为主瓶颈。Kubernetes 也提供了并行拉镜像的能力开关
（serializeImagePulls 与 maxParallelImagePulls）。

`T_model_artifact` 是模型工件到达本地可读路径的时间——从对象存储下载、从模型仓库
拉取、或从 OCI 工件挂载和解包。KServe 的文档明确指出：传统从 S3/URI 拉模型对小模型
足够，但对大模型会成为瓶颈，显著拖慢自动扩展下的启动时间。

`T_runtime_init` 是 GPU 驱动与运行时初始化、框架库加载、首次 CUDA 相关开销。

`T_warmup_compile` 是首次推理、首次图编译、首次 TensorRT 构建等一次性成本。如果没有
缓存复用，这些成本会在每次 Pod 重建时反复出现。

把这些段落与 Kubernetes 的可观测信号绑定是关键：`PodScheduled`、`Initialized`、
`Ready` 等条件本身都有时间戳；对 AI 特有的 `ModelLoaded`、`WarmupDone` 则可以通过
自定义 condition 写回 PodStatus，从而让"AI 业务就绪"在编排层面可见、可监控、
可告警。

## 调度与硬件局部性：GPU 不是一个数字

很多"GPU Pod 冷启动"文章把调度写成一句话："申请 nvidia.com/gpu 就行"。在单卡推理
上这往往成立，但一旦进入多卡推理/训练、MIG 切分、NUMA 对齐、共享 GPU，就会出现两类
直接影响启动速度的问题：调度路径更复杂，以及调度后在节点侧失败/重试。

首先要理解 Kubernetes 的 device plugin 框架。厂商把硬件以扩展资源的形式上报给
kubelet，再由 kubelet 更新到 NodeStatus 中。但"硬件局部性"并不天然等价于
"节点级可用"。以 NUMA 为例，Topology Manager 的目标是把 CPU、设备等资源尽可能对齐
到同一 NUMA 域；但调度器并不具备拓扑感知，因此可能出现"Pod 被调度到某节点，但最终
在节点侧因为 Topology Manager 而失败"的情况。这种失败会带来重试与启动时间抖动。

在集群层面，为了避免"节点侧 AdmissionError"造成的启动抖动，一些平台会把 NUMA/GPU
拓扑信息上报到调度层参与打分或约束。阿里云 ACK 的实践表明：仅依赖 kubelet 的 CPU
policy 与 NUMA topology policy，在集群里会遇到"调度器不知道 NUMA 内部剩余 CPU/GPU
是否满足 QoS"的问题，导致大量 Pod 调度后进入 AdmissionError。启用 NUMA 拓扑感知调度
后，某些场景下模型加载耗时可从约 15.9s 降到约 5.4s（结果因环境而异）。

接下来是 DRA（Dynamic Resource Allocation）。DRA 的价值不只是"又一种申请 GPU 的方式"，
而是把"设备类 + 选择器 + claim"引入调度与分配。Kubernetes 官方文档定义 DRA 为一种在
Pod 之间请求和共享设备资源（常见是硬件加速器）的机制：设备驱动与管理员定义 device
classes，Kubernetes 把匹配设备分配给 claim，并把 Pod 放到能访问这些设备的节点上。DRA
把"拓扑/型号/容量"等约束从"节点标签拼装 + 手工亲和性"提升为"声明式设备选择"。

此外，GPU 的共享策略也会影响启动与稳定性。以 NVIDIA GPU Operator 的 time-slicing 为例，
它通过把一个物理 GPU 变成多个"副本"供 Pod 领取来实现 oversubscription，但这类共享不
具备 MIG 的硬件内存和故障隔离能力。这些事实都会影响你如何定义"Ready"以及如何做
warmup 与隔离策略，从而间接影响冷启动体验。

## 镜像与模型分发：把大文件从关键路径搬走

AI Pod 的"下载面"通常有两层：容器镜像与模型工件。这两层往往都很大，而且都可能落在
关键路径上。优化的核心思想可以概括为一句话：能预置就预置，能缓存就缓存，能按需就按需。

在容器镜像层面，Kubernetes 本身提供了并行拉取策略：将 kubelet 的
`serializeImagePulls` 设为 false 即可启用跨 Pod 并行拉镜像，并通过
`maxParallelImagePulls` 限制并发，防止拉镜像把网络或磁盘 I/O 打满。需要注意的是，
kubelet 不会为同一个 Pod 内的多个容器并行拉镜像。

更激进的路线是 lazy pulling / remote snapshot。stargz snapshotter 的做法是"直接从
远端挂载 rootfs 层而不是下载并解包全部内容"——允许在镜像内容尚未完全落盘时就启动容器，
按需再取真正访问到的内容。nydus-snapshotter 也采用类似思路：容器即使镜像只部分可用
也能运行，后续按需拉取必要数据块。对于动辄数 GB 的 AI 镜像来说，这个优化可以把镜像
拉取从分钟级缩短到秒级。

在模型工件层面，KServe 定义了"storage initializer 作为 init container 下载模型到
本地目录"的标准模式。在 OCI modelcar 方案中，KServe v0.14 进一步做了关键优化：早期
modelcar 作为 sidecar 时无法保证模型容器先启动，后来改为将 OCI 模型容器配置为 init
container，确保模型镜像先被抓取再启动主容器。同时引入"Model Cache"概念，用节点本地
存储缓存大模型，以缩短 LLM Pod 的启动时间。

如果你不使用 KServe，也可以走 Kubernetes 原生路线。第一种是把模型打包成 OCI 工件，
让模型"像镜像一样"被分发与缓存，受益于节点本地镜像缓存与层复用。第二种是直接用 OCI
工件挂载为卷——Kubernetes 的 image volumes（v1.35 beta，默认启用）允许把 OCI registry
的内容挂载进容器文件系统，作为 volume 消费。对于需要大量只读权重文件的场景，它提供了
一个比"应用启动后再去下载"更靠前、更可控的载入点。

在模型仓库与缓存层面，如果使用 Hugging Face Hub 的生态，最容易忽视的启动项其实是
"重复下载与重复解压"。huggingface_hub 的默认缓存目录在 `~/.cache/huggingface/hub`，
可通过 `HF_HOME` 或 `HF_HUB_CACHE` 等环境变量改到更快的路径（比如节点本地 NVMe 或
可共享的只读缓存卷）。

最后是模型格式本身。Safetensors 被定位为"安全（相对 pickle）且快速（zero-copy）"
的张量存储格式，支持只加载部分张量（对多 GPU/分片加载尤其有意义）。相比之下，PyTorch
的 torch.save 使用 Python pickle 做序列化，torch.load 使用 pickle 反序列化；pickle
的可执行反序列化风险也被供应链安全研究反复强调——加载不可信模型文件可能导致任意代码
执行。如果你的目标是"极致缩短权重进入 GPU 的时间"，vLLM 文档提到 fastsafetensors
能利用 GPU Direct Storage 直接把权重加载到 GPU memory，绕开 CPU 中转。

## 运行时初始化与编译缓存：减少"第一次"的罚时

AI Pod 冷启动的另一个"隐形大头"是一次性初始化成本。它不是单点慢，而是多个
"第一次"叠加：第一次触发 GPU 初始化、第一次触发 CUDA JIT、第一次触发框架编译、
第一次触发推理引擎的图优化与 kernel 生成。

GPU 初始化方面，NVIDIA 的 Driver Persistence 文档描述了一个具体且可操作的事实：在
Linux 的无图形/短作业场景下，GPU 可能会在每次作业启动时初始化，作业结束后又去初始化；
应用触发 GPU 初始化时可能产生每块 GPU 约 1-3 秒的启动成本（文档将其归因于 ECC
scrubbing），并给出 persistence mode / persistence daemon 以保持 GPU 初始化状态。
在 nvidia-smi 中，persistence mode 的定义是"即使没有活跃 client，驱动仍保持加载，
从而最小化 driver load latency"。

CUDA JIT 方面，CUDA 的 compute cache 机制会在 JIT 编译 PTX 后缓存生成的二进制以避免
重复编译。环境变量 `CUDA_CACHE_PATH` 和 `CUDA_CACHE_MAXSIZE` 可以控制缓存位置与
大小。这里有一个与冷启动强相关的坑：如果默认缓存目录在慢的网络 home 上，可能导致非常
长的应用启动时间——此时应将 `CUDA_CACHE_PATH` 指向更快的文件系统。

框架编译方面，PyTorch 的 torch.compile 缓存会写入 `TORCHINDUCTOR_CACHE_DIR`（默认
类似 `/tmp/torchinductor_<user>`）。对容器化部署而言，默认缓存容易随 Pod 消失。如果
你把它挂到持久卷或节点本地持久路径，并在滚动升级/弹性扩缩时复用，就能把"每次冷启动
都要编译"的成本降为"每种硬件/模型版本首次编译一次"。

推理引擎方面，TensorRT 的架构文档提供了一个直接的初始化加速选项：CUDA lazy loading
（`CUDA_MODULE_LOADING=LAZY`）可以显著降低 TensorRT 的峰值 GPU/host 内存使用并加速
初始化，性能影响可忽略（约 <1%）。如果走 ONNX Runtime + TensorRT EP 路线，文档把
"cache" 作为核心能力强调：TensorRT EP 的 cache 可以把 session creation time 从
分钟级降到秒级；TensorRT RTX EP 进一步提供 runtime cache，为每个 engine 缓存 JIT
编译出的 CUDA kernels，后续加载时反序列化预编译内核以降低 session load time。

把这一节归纳成一条工程原则：把一次性成本（driver init / JIT / compile / engine
build）显式地外置为可复用的缓存资产，并让它在 Pod 重建与扩缩容过程中持续命中。

## 预热与弹性：Pod 池、模型 warmup 与成本权衡

当你解决了"下载面"和"第一次初始化面"，就进入最后一个问题：如何让系统在突发流量
下仍然能"秒级扩展"，同时不让成本爆炸。这里建议从一个三角形来思考：延迟、成本、
复杂度——每种预热手段在三者上位置不同。

从"把首请求延迟移走"的角度，推理服务自带 warmup 是最直接的方案。以 Triton 为例，
它的 ModelWarmup 机制允许服务端在对外提供服务前执行一系列 warmup 推理请求，只有当
模型实例成功完成 warmup 后才会对外提供服务。某些后端的初始化可能延迟到第一次推理时
才发生（如 TF-TRT 的优化），ModelWarmup 把这些不可预测的延迟从客户端侧移走。

把 warmup 与 Kubernetes 的 Ready 语义对齐，是 AI 版启动优化最应该强调的写法：用
readinessGates 或 readinessProbe 让 Pod 在 warmup 完成前不进入负载均衡池，从机制上
保证"首请求不当小白鼠"。

从"把扩容等待移走"的角度，节点/容量预留是另一个高收益杠杆。Kubernetes 官方文档把
node overprovisioning 定义为：用负优先级的 placeholder Pods 预占一部分计算资源，从而
在扩容事件中减少新 Pod 进入 Pending 的时间。AWS EKS 的最佳实践文档也指出：Cluster
Autoscaler 为了省成本会让 Pod 等待节点扩容，而节点可能需要数分钟才能可用，用
overprovisioning 可以用成本换延迟。

但 GPU 场景还有一个特殊等待项：加速器 device plugin 在扩容时可能需要数分钟才能把
资源上报，导致 Pod 即便等到了新节点仍不能立即调度，甚至可能触发重复扩容。这意味着
AI 场景的"预热"不应只盯着 Pod 内 warmup，也要盯住节点侧的 GPU 栈就绪——驱动、
容器运行时、device plugin、资源上报的整条链路。

从"把模型分发移走"的角度，KServe 的演进提供了一个体系化案例：modelcars 通过 OCI
模型工件复用镜像分发与缓存；为解决 sidecar 启动顺序不确定的问题，又将 OCI 模型容器
作为 init container 预抓取；进一步引入本地模型缓存缩短 LLM Pod 启动。可以抽象成一个
通用结论：AI 预热不仅是"发几次空请求"，更是"围绕模型工件建立可复用的分发与缓存层"。

GKE 的 Agent Sandbox 则从另一个维度切入预热问题。它将 gVisor 安全沙箱与容器快照技术
结合，在初始化阶段为完全配置好的容器（包含依赖库、运行时状态、预加载模型）创建
gVisor 快照，当新请求到达时可以在几百毫秒内从快照恢复新实例。相比传统冷启动，Agent
Sandbox 可实现高达 90% 的启动时间改善，同时保持 gVisor 沙箱级别的安全隔离。这对
LLM Agent、Serverless AI、多租户 AI 服务等需要快速启动与强隔离的场景尤其有价值。

## 收束：三类容易被忽视的关键杠杆

把上面的内容收束，除了大家常提到的"调度/模型加载/预热"三板斧之外，至少还有三类
往往更影响端到端冷启动的杠杆：

第一是容量供给与节点侧加速器栈就绪。节点扩容可能分钟级，device plugin 上报可能也
分钟级，两者叠加后 Pod Pending 时间远超预期。

第二是镜像/模型分发的关键路径搬迁。并行拉取、lazy pulling、OCI 工件化、节点本地缓存
——核心思想都是"不要让用户的首请求等文件 IO"。

第三是一次性初始化与编译缓存复用。driver persistence、CUDA/JIT cache、torch.compile
cache、推理引擎 cache——把"第一次"的成本变成可复用的资产。

把这三类杠杆与常规的调度优化、模型格式优化、服务 warmup 组合在一起，才构成 AI Pod
冷启动优化的完整关键路径。

---

## 相关资源

<a href="https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/">
Kubernetes Pod Lifecycle</a>

<a href="https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/">
Dynamic Resource Allocation (DRA)</a>

<a href="https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/">
Scheduling GPUs</a>

<a href="https://docs.nvidia.com/deploy/driver-persistence/index.html">
NVIDIA Driver Persistence</a>

<a href="https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/">
CUDA Best Practices Guide</a>

<a href="https://pytorch.org/docs/stable/torch.compiler_faq.html">
PyTorch torch.compile FAQ</a>

<a href="https://huggingface.co/docs/safetensors/index">Safetensors</a>

<a href="https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html">
ONNX Runtime TensorRT EP</a>

<a href="https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/model_configuration.html">
Triton Model Configuration (ModelWarmup)</a>

<a href="https://kserve.github.io/website/latest/">KServe Documentation</a>

<a href="https://github.com/containerd/stargz-snapshotter">
Stargz Snapshotter</a>

<a href="https://github.com/containerd/nydus-snapshotter">
Nydus Snapshotter</a>

<a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
GKE Agent Sandbox</a>
