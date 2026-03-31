# DaoCloud 云原生开源案例（架构重整版）

## 参考输入

- DaoCloud Profile README: https://github.com/DaoCloud/.github/blob/main/profile/README.md

## 架构分层视角（你给定的结构）

- 多云组件（最上层）：`Clusterpedia`
- Kubernetes 平台层（3 层）：
  - 1. 调度编排层：`LWS`、`Kueue`（`llm-d` 使用 `LWS`）
  - 2. 网络存储层：`Spiderpool(CNI)`、`Hwameistor(存储)`、`merbridge(mesh)`
  - 3. 资源管理层：`HAMi`、`containerd`
- AI 引擎层：`vLLM`（并与 `llm-d` 协同）
- 安装与测试链路：`kubean -> kubespray -> kubeadm`，`kwok` 作为测试组件

## 可编辑生态图（Mermaid）

```mermaid
flowchart TB
  subgraph GLOBAL["全局 / 多集群层"]
    KAR["⭐ Karmada<br/>多集群编排 / 调度"]
    CP["Clusterpedia<br/>多集群同步 / 检索 / 统一视图"]
  end

  subgraph AICP["AI Serving Control Plane"]
    LLMD["llm-d<br/>分布式推理编排"]
    AIB["⭐ AIBrix<br/>推理基础设施 / Gateway / KV Cache / Routing"]
    SR["Semantic Router<br/>语义路由 / MoM"]
  end

  subgraph ENGINE["AI 引擎层"]
    VLLM["⭐ vLLM<br/>推理引擎"]
  end

  subgraph ORCH["Kubernetes 工作负载编排层"]
    LWS["LWS"]
    KUEUE["Kueue<br/>Queue / Quota / Admission"]
  end

  subgraph EXT["Kubernetes 平台扩展层"]
    SP["Spiderpool<br/>CNI / IPAM"]
    HW["Hwameistor<br/>CSI / Storage"]
    MB["merbridge<br/>Mesh Dataplane Enhance"]
    HAMI["HAMi<br/>GPU / 异构资源管理"]
    ISTIO["Istio"]
  end

  subgraph CORE["Kubernetes 核心层"]
    APIS["API Server"]
    SCH["Scheduler"]
    KLET["Kubelet"]
  end

  subgraph NODE["节点运行时层"]
    CTD["containerd"]
  end

  subgraph EDGE["边缘扩展分支"]
    KE["⭐ KubeEdge<br/>Cloud-Edge Extension"]
    EN["Edge Nodes / Devices"]
  end

  %% Global
  KAR --> APIS
  CP -. 对接 / 检索 .-> APIS
  CP -. 可对接 .-> KAR

  %% AI control plane
  LLMD --> LWS
  LLMD --> VLLM
  AIB --> VLLM
  AIB --> APIS
  SR --> AIB
  SR --> VLLM

  %% Orchestration
  LWS --> APIS
  KUEUE --> APIS
  KUEUE -. 与标准调度器协同 .-> SCH

  %% Extensions
  SP --> KLET
  HW --> KLET
  HAMI --> SCH
  MB --> ISTIO
  ISTIO --> APIS

  %% Core to runtime
  APIS --> SCH
  APIS --> KLET
  KLET --> CTD

  %% Edge
  APIS --> KE
  KE --> EN

  classDef top fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef mid fill:#eef4ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef core fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.2px;

  class KAR,AIB,VLLM,KE top;
  class CP,LLMD,SR,LWS,KUEUE,SP,HW,MB,HAMI,ISTIO,CTD,EN mid;
  class APIS,SCH,KLET core;
```

## 项目清单（按架构分层）

### 多云组件（顶层）

- [⭐ clusterpedia-io/clusterpedia](https://github.com/clusterpedia-io/clusterpedia)

### AI 引擎层

- [⭐ vllm-project/vllm](https://github.com/vllm-project/vllm)
- [llm-d/llm-d](https://github.com/llm-d/llm-d)

### Kubernetes 平台层

#### 调度编排层

- [kubernetes-sigs/lws](https://github.com/kubernetes-sigs/lws)
- [kubernetes-sigs/kueue](https://github.com/kubernetes-sigs/kueue)

#### 网络存储层

- [⭐ spidernet-io/spiderpool](https://github.com/spidernet-io/spiderpool)
- [hwameistor/hwameistor](https://github.com/hwameistor/hwameistor)
- [merbridge/merbridge](https://github.com/merbridge/merbridge)
- [istio/istio](https://github.com/istio/istio)

#### 资源管理层

- [⭐ Project-HAMi/HAMi](https://github.com/Project-HAMi/HAMi)
- [containerd/containerd](https://github.com/containerd/containerd)

#### 底座

- [⭐ kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)

### 安装与测试组件

- [⭐ kubean-io/kubean](https://github.com/kubean-io/kubean)
- [kubernetes-sigs/kubespray](https://github.com/kubernetes-sigs/kubespray)
- [kubernetes/kubeadm](https://github.com/kubernetes/kubeadm)
- [kubernetes-sigs/kwok](https://github.com/kubernetes-sigs/kwok)

### 其他 DaoCloud 相关项目（补充）

- [knoway-dev/knoway](https://github.com/knoway-dev/knoway)
- [kdoctor-io/kdoctor](https://github.com/kdoctor-io/kdoctor)
