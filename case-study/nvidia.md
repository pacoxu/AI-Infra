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
    KDP["k8s-device-plugin"]
    DCGM["dcgm-exporter"]
    AICR["AI Cluster Runtime (AICR)"]
  end

  subgraph RES["资源建模 / 调度 / 故障治理"]
    DRA["⭐ GPU DRA Driver"]
    KAI["⭐ KAI Scheduler"]
    NVS["NVSentinel"]
  end

  subgraph SERVE["推理编排与服务"]
    DYN["⭐ Dynamo"]
    TRT["TensorRT-LLM"]
    TRITON["Triton Inference Server"]
  end

  subgraph COMM["高性能通信基础"]
    NCCL["NCCL"]
  end

  %% foundation
  K8S --> GPO
  K8S --> DRA
  K8S --> KAI
  K8S --> NVS
  K8S --> DYN
  CTD --> CTK

  %% ops layer
  GPO --> CTK
  GPO --> KDP
  GPO --> DCGM
  AICR --> GPO
  GPO -. "集成入口" .-> DRA

  %% resource / scheduling / remediation
  KDP -. "从设备暴露走向\n更细粒度资源建模" .-> DRA
  DRA -. "资源声明 / 共享 / 拓扑信息" .-> KAI
  DCGM -. "健康信号 / 指标输入" .-> NVS

  %% serving
  DYN --> TRT
  DYN --> TRITON
  TRT -. "可作为 Triton backend\n也可直接使用" .-> TRITON

  %% comms
  NCCL -. "多 GPU / 多节点通信" .-> TRT
  NCCL -. "分布式通信基础" .-> DYN

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.4px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef base fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.2px;

  class KAI,DRA,DYN star;
  class GPO,CTK,KDP,DCGM,AICR,NVS,TRT,TRITON,NCCL normal;
  class K8S,CTD base;
```

## 发起/主导项目（代表）

- [⭐ ai-dynamo/dynamo](https://github.com/ai-dynamo/dynamo)
- [⭐ kai-scheduler/KAI-Scheduler](https://github.com/kai-scheduler/KAI-Scheduler)
- [⭐ NVIDIA/k8s-dra-driver-gpu](https://github.com/NVIDIA/k8s-dra-driver-gpu)
- [NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator)
- [NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin)
- [NVIDIA/dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter)
- [NVIDIA/nvidia-container-toolkit](https://github.com/NVIDIA/nvidia-container-toolkit)
- [NVIDIA/NVSentinel](https://github.com/NVIDIA/NVSentinel)
- [NVIDIA/aicr](https://github.com/NVIDIA/aicr)
- [NVIDIA/TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM)
- [triton-inference-server/server](https://github.com/triton-inference-server/server)
- [NVIDIA/nccl](https://github.com/NVIDIA/nccl)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [containerd/containerd](https://github.com/containerd/containerd)
