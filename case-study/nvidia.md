# NVIDIA 云原生开源案例（全景版）

## 参考输入

- 你提供的图片（NVIDIA ❤️ Kubernetes 时间线）
- 当前仓库 `nvidia` 项目清单

## 可编辑云原生开源全景图（Mermaid）

```mermaid
flowchart LR
  subgraph UP["上游基座（深度参与）"]
    K8S["Kubernetes"]
    CTD["containerd"]
  end

  subgraph OPS["GPU 接入与集群运维"]
    GPO["GPU Operator"]
    CTK["NVIDIA Container Toolkit"]
    NVRC["NVRC<br/>microVM PID 1"]
    KDP["k8s-device-plugin"]
    DCGM["dcgm-exporter"]
    AICR["AI Cluster Runtime (AICR)"]
  end

  subgraph RES["资源建模 / 调度 / 故障治理"]
    DRA["⭐ GPU DRA Driver"]
    KAI["⭐ KAI Scheduler"]
    NVS["NVSentinel"]
  end

  subgraph ORCH["多角色工作负载抽象"]
    GROVE["⭐ Grove"]
    LWS["LWS"]
  end

  subgraph SERVE["推理控制面 / 服务编排"]
    DYN["⭐ Dynamo"]
    LLMD["llm-d"]
    TRT["TensorRT-LLM"]
    TRITON["Triton Inference Server"]
  end

  subgraph STATE["KV 状态面 / 数据搬运"]
    KVBM["⭐ KVBM<br/>KV Block Manager"]
    KVCR["KVCR<br/>KV Cache Runner"]
    NIXL["NIXL"]
    NCCL["NCCL"]
  end

  subgraph MODEL["模型仓库 / 权重分发"]
    MXH["MatrixHub<br/>HF-compatible private model hub"]
  end

  %% foundation
  K8S --> GPO
  K8S --> DRA
  K8S --> KAI
  K8S --> NVS
  K8S --> GROVE
  K8S --> LWS
  K8S --> DYN
  CTD --> CTK
  CTD -. "Kata Containers<br/>microVM 路径" .-> NVRC

  %% ops layer
  GPO --> CTK
  GPO --> KDP
  GPO --> DCGM
  NVRC -. "启动 GPU 管理守护进程" .-> DCGM
  AICR --> GPO
  GPO -. "集成入口" .-> DRA

  %% resource / scheduling / remediation
  KDP -. "从设备暴露走向\n更细粒度资源建模" .-> DRA
  DRA -. "资源声明 / 共享 / 拓扑信息" .-> KAI
  DCGM -. "健康信号 / 指标输入" .-> NVS

  %% workload / orchestration
  DYN --> GROVE
  GROVE -. "层次化 gang /\n启动顺序 / 拓扑约束" .-> KAI
  LWS -. "社区原生多角色 workload API" .-> GROVE

  %% serving / state plane
  DYN --> KVBM
  DYN -. "KV Router inventory / hints" .-> KVCR
  DYN --> TRT
  DYN --> TRITON
  MXH -. "HF_ENDPOINT / 预缓存模型" .-> DYN
  LLMD -. "社区侧 distributed serving\nPD / KV-aware routing" .-> DYN
  LLMD -. "双 LWS / 社区路径" .-> LWS
  KVBM -. "KV block 生命周期 /\n分层 offload" .-> NIXL
  KVCR -. "跨层 / 跨节点传输" .-> NIXL
  DYN -. "KV / prefix 传输" .-> NIXL
  TRT -. "可作为 Triton backend\n也可直接使用" .-> TRITON

  %% comms
  NIXL -. "分布式 KV / prefix data plane" .-> DYN
  NIXL -. "远端 KV 可见性 /\n跨节点搬运" .-> KVBM
  NCCL -. "多 GPU / 多节点通信" .-> TRT
  NCCL -. "分布式通信基础" .-> DYN

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.4px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef base fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.2px;
  classDef bridge fill:#f5f3ff,stroke:#7c3aed,color:#4c1d95,stroke-width:1.1px;

  class KAI,DRA,DYN,GROVE,KVBM star;
  class GPO,CTK,NVRC,KDP,DCGM,AICR,NVS,TRT,TRITON,KVCR,NIXL,NCCL normal;
  class LLMD,LWS,MXH bridge;
  class K8S,CTD base;
```

## 发起/主导项目（代表）

- [⭐ ai-dynamo/dynamo](https://github.com/ai-dynamo/dynamo)
- [⭐ ai-dynamo/grove](https://github.com/ai-dynamo/grove)
- [ai-dynamo/nixl](https://github.com/ai-dynamo/nixl)
- [ai-dynamo/kvcr](https://github.com/ai-dynamo/kvcr) — KV Cache Runner（活跃开发中）
- [⭐ kai-scheduler/KAI-Scheduler](https://github.com/kai-scheduler/KAI-Scheduler)
- [⭐ kubernetes-sigs/dra-driver-nvidia-gpu](https://github.com/kubernetes-sigs/dra-driver-nvidia-gpu)
- [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator)
- [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [NVIDIA/dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter)
- [NVIDIA/nvidia-container-toolkit](https://github.com/NVIDIA/nvidia-container-toolkit)
- [NVIDIA/nvrc](https://github.com/NVIDIA/nvrc) — NVIDIA Runtime Container Init，
  Kata Containers GPU microVM 内的最小 PID 1
- [NVIDIA/NVSentinel](https://github.com/NVIDIA/NVSentinel)
- [NVIDIA/aicr](https://github.com/NVIDIA/aicr)
- [NVIDIA/TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM)
- [triton-inference-server/server](https://github.com/triton-inference-server/server)
- [NVIDIA/nccl](https://github.com/NVIDIA/nccl)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [containerd/containerd](https://github.com/containerd/containerd)

## MatrixHub：模型仓库与 Dynamo 的衔接

[`MatrixHub`](https://github.com/matrixhub-ai/matrixhub) 是开源、自托管、
兼容 Hugging Face API 的模型仓库。Dynamo 可以通过 `HF_ENDPOINT` 指向集群内的
MatrixHub，从预缓存的内部端点下载模型，而不必让每个 worker 重复访问公共
Hugging Face 服务。

这条路径补充的是模型权重的来源、治理和集群内下载入口，不属于 KV cache 数据面：

```text
Hugging Face / 私有模型 -> MatrixHub -> Dynamo worker -> inference engine
```

MatrixHub 负责私有模型仓库、代理缓存和分发入口；Dynamo 继续负责推理编排与运行时。

## 补充主线：Dynamo / Grove / KAI / KVBM / KVCR

这条线现在更适合理解成：

```text
Dynamo -> Grove -> KAI Scheduler -> GPU DRA Driver
          \-> KVBM -> NIXL
          \-> KV Router -> KVCR -> NIXL
```

它们不是一组并列竞争项目，而是从推理系统意图一路落到工作负载抽象、调度策略、
资源模型和 KV 状态面的主链路。

| 组件 | 在图中的位置 | 主要职责 |
| --- | --- | --- |
| `Dynamo` | 推理控制面 / 服务编排 | 作为 NVIDIA 的 distributed inference control plane，承接 `DGDR/DGD`、Planner、Router、Profiler 等平台入口 |
| `Grove` | 多角色工作负载抽象 | 用 `PodCliqueSet / PodGang` 一类 API 把 `prefill / decode / router / worker` 表达成单个 Kubernetes 对象 |
| `KAI Scheduler` | 调度策略层 | 负责 gang、拓扑感知、层次队列、公平性和 DRA support，把 Grove 的编排意图落成真正的放置决策 |
| `KVBM` | KV 状态面 | 管理 KV block 生命周期、跨节点复用与 `HBM -> host -> SSD -> remote` 分层 offload，和 `NIXL` 一起构成 Dynamo 的 KV state plane |
| `KVCR` | KV cache runtime | 根据 KV Router hints 管理本地 DRAM、SSD 和对象存储驻留，通过 NIXL 完成跨层与跨节点传输，并以 KVCR-Guard 提供可选故障恢复能力 |

这里最容易被漏掉的是 `KVBM`：它不是独立 repo，而是 `Dynamo` 内部非常关键的系统层。
如果不把它画出来，`Dynamo` 看起来就会像“又一个推理部署器”，而不是一个把 KV 生命周期、
路由和多节点 serving 一起组织起来的平台。

`KVCR` 则是独立仓库中的新方向：把全局 cache inventory 和路由决策留给 KV-aware router，
自身聚焦本地 cache policy、驻留与数据搬运。它同时强调 framework/router agnostic，当前仍处于
活跃开发阶段，官方尚不建议用于生产环境；因此这里先把它与 `KVBM` 并列展示，不直接定义为
替代关系。

## 与 llm-d 的交叉补充

`llm-d` 不属于 NVIDIA 私有主线，但它是理解 NVIDIA 这条路线时非常好的社区对照组。
更准确地说：

- `Dynamo` 更接近 **performance-first inference platform**
- `llm-d` 更接近 **Kubernetes-native distributed serving stack**
- `Grove` 和 `LWS` 处在相近的 workload abstraction 位置，但前者更强意见、后者更社区原生

| 维度 | NVIDIA 主线 | `llm-d` 路线 |
| --- | --- | --- |
| 控制面 / serving stack | `Dynamo` | `llm-d` |
| 多角色 workload API | `Grove` | `LWS`（双 `LeaderWorkerSet` 路径） |
| 调度与拓扑 | `KAI + GPU DRA Driver`，更强调 GPU / ComputeDomain / fabric 拓扑 | 更偏社区调度生态组合，常与 `KServe`、Gateway API、Kubernetes 原生 workload API 协同 |
| KV 路径 | `KVBM / KVCR + NIXL`，把 KV 复用、offload、远端传输做成系统级 state plane | 更强调 KV-aware routing、PD serving 和 serving stack 集成 |
| 硬件姿态 | 更偏 NVIDIA 一体化优化 | 更偏中立，更容易成为跨厂商 distributed serving 基线 |

所以把 `llm-d` 交叉补进 NVIDIA 全景图的价值，不是说它和 `Dynamo` 是同一项目，而是能把
两条路线的分层关系看得更清楚：

- NVIDIA 主线的辨识度在 `Grove + KAI Scheduler + GPU DRA Driver + KVBM / KVCR`
- 社区主线的辨识度在 `llm-d + LWS + KServe / Gateway API` 这类更上游、更中立的组合

## 生态交叉项目入口

- [llm-d/llm-d](https://github.com/llm-d/llm-d)
- [matrixhub-ai/matrixhub](https://github.com/matrixhub-ai/matrixhub)
- [Dynamo: Load Models from MatrixHub](https://docs.nvidia.com/dynamo/dev/kubernetes/model-deployment/model-loading/matrix-hub)
- [Dynamo KVBM README](https://github.com/ai-dynamo/dynamo/blob/main/lib/bindings/kvbm/README.md)
- [KVCR design overview](https://github.com/ai-dynamo/kvcr/blob/main/docs/design_overview.md)

## 延伸阅读

- [Dynamo 架构全景](../docs/inference/dynamo.md)
- [模型分发全景：MatrixHub、Harbor、Dragonfly、ModelPack 与 ModelExpress](../docs/inference/model-distribution-stack.md)
- [Grove: Kubernetes API for Inference Orchestration](../docs/inference/grove.md)
- [NVIDIA 推理编排主线拆解：Dynamo、Grove、KAI Scheduler 与 GPU DRA Driver](../docs/blog/2026-05-11/2026-05-11-dynamo-grove-kai-dra-ecosystem-zh.md)
- [推理编排方案如何选择？AIBrix、Kthena、Dynamo、llm-d、KServe、vLLM Production Stack 与 SGLang/RBG](../docs/blog/2026-05-13/2026-05-13-how-to-choose-inference-orchestration-stacks_zh.md)
