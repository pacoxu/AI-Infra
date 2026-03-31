# NVIDIA 云原生开源案例（全景版）

## 参考输入

- 你提供的图片（NVIDIA ❤️ Kubernetes 时间线）
- 当前仓库 `nvidia` 项目清单

## 可编辑云原生开源全景图（Mermaid）

```mermaid
flowchart TB
  subgraph TL["时间演进（结合图片）"]
    T2017["2017"]
    T2025["2025"]
    TNOW["当前阶段"]
    T2017 --> T2025 --> TNOW
  end

  subgraph BASE["Kubernetes 基座"]
    K8S["Kubernetes"]
    CTD["containerd"]
  end

  subgraph RUNTIME["GPU 运行时与集群运维"]
    CTK["NVIDIA Container Toolkit"]
    GPO["GPU Operator"]
    KDP["k8s-device-plugin"]
    DCGM["dcgm-exporter"]
    AICR["AI Cluster Runtime (AICR)"]
  end

  subgraph SCHED["调度与资源分配（K8s 集成）"]
    KAI["⭐ KAI Scheduler"]
    DRA["⭐ GPU DRA Driver"]
    NVS["NVSentinel"]
  end

  subgraph INFER["推理与加速栈"]
    DYN["⭐ Dynamo Inference Framework"]
    TRT["TensorRT-LLM"]
    TRITON["Triton Inference Server"]
    NCCL["NCCL"]
  end

  %% timeline mapping
  T2017 -.-> CTK
  T2017 -.-> GPO
  T2025 -.-> KAI
  T2025 -.-> DYN
  T2025 -.-> NVS
  T2025 -.-> DRA
  TNOW -.-> AICR

  %% base relations
  CTD --> K8S
  CTK --> CTD
  GPO --> K8S
  KDP --> GPO
  DCGM --> GPO
  AICR --> GPO
  AICR --> K8S

  %% scheduler/resource
  KAI --> K8S
  DRA --> K8S
  NVS --> DRA

  %% inference stack
  DYN --> TRITON
  DYN --> TRT
  DYN --> K8S
  NCCL --> DYN
  TRT --> TRITON

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef base fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.2px;

  class KAI,DRA,DYN star;
  class CTK,GPO,KDP,DCGM,AICR,NVS,TRT,TRITON,NCCL normal;
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
