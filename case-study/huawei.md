# 华为云（Huawei）云原生开源案例（初稿）

## 分析基线

- 对照基线：字节分层方案（你提供的链接 + 分层图）
- 本文聚焦你点名的华为相关项目：`Karmada`、`Volcano`（含 `kthena/agentcube`）、`KubeEdge`、`kmesh`、`kuasar`、`vllm-ascend`、`openGemini`、`Sermant`

## 与字节方案的分层对照（简版）

- 多集群与联邦：字节 `kubeadmiral/podseidon`；华为 `Karmada`
- 调度与编排：字节 `godel-scheduler`；华为 `Volcano`（并扩展 `kthena/agentcube`）
- 节点/运行时与边云：字节 `katalyst-core`；华为 `KubeEdge`、`kuasar`
- 服务治理：字节 `kubegateway/kubezoo`；华为 `kmesh`、`Sermant`
- 可观测/数据底座：字节 `kelemetry`；华为 `openGemini`
- AI 推理适配：华为侧代表项目 `vllm-ascend`

## 可编辑生态图（Mermaid）

```mermaid
flowchart TB
  subgraph Foundation["社区基础（早期深度参与）"]
    K8S["Kubernetes"]
    ISTIO["Istio"]
  end

  subgraph HuaweiEco["华为云原生开源生态"]
    direction TB

    subgraph MC["多集群与调度"]
      KARMADA["Karmada<br/>多集群编排与联邦"]
      VOLCANO["Volcano<br/>批处理/Gang 调度"]
      KTHENA["Kthena<br/>Volcano 生态 AI Serving 编排"]
      AGENTCUBE["AgentCube<br/>Volcano 生态 Agent 编排"]
    end

    subgraph ER["边云与运行时"]
      KUBEEDGE["KubeEdge<br/>边云协同"]
      KUASAR["kuasar<br/>轻量隔离容器运行时"]
    end

    subgraph SG["服务治理与流量"]
      KMESH["kmesh<br/>eBPF Service Mesh 数据面"]
      SERMANT["Sermant<br/>服务治理/无损治理"]
    end

    subgraph DO["数据与可观测"]
      OPENG["openGemini<br/>时序数据与可观测存储"]
    end

    subgraph AI["AI 推理适配"]
      VLLMA["vLLM Ascend<br/>Ascend NPU 推理后端适配"]
    end
  end

  K8S --> KARMADA
  K8S --> VOLCANO
  K8S --> KUBEEDGE
  K8S --> KUASAR
  ISTIO --> KMESH
  ISTIO --> SERMANT

  VOLCANO --> KTHENA
  VOLCANO --> AGENTCUBE
  KARMADA --> VOLCANO
  KARMADA --> KUBEEDGE

  VOLCANO --> VLLMA
  KMESH --> SERMANT
  OPENG -. metrics/traces .-> SERMANT
  OPENG -. observability .-> KARMADA
  OPENG -. observability .-> VOLCANO

  classDef foundation fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef huawei fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;

  class K8S,ISTIO foundation;
  class KARMADA,VOLCANO,KTHENA,AGENTCUBE,KUBEEDGE,KUASAR,KMESH,SERMANT,OPENG,VLLMA huawei;
```

## 发起/主导项目（代表）

- [karmada-io/karmada](https://github.com/karmada-io/karmada)
- [volcano-sh/volcano](https://github.com/volcano-sh/volcano)
- [volcano-sh/kthena](https://github.com/volcano-sh/kthena)
- [volcano-sh/agentcube](https://github.com/volcano-sh/agentcube)
- [kubeedge/kubeedge](https://github.com/kubeedge/kubeedge)
- [kmesh-net/kmesh](https://github.com/kmesh-net/kmesh)
- [kuasar-io/kuasar](https://github.com/kuasar-io/kuasar)
- [vllm-project/vllm-ascend](https://github.com/vllm-project/vllm-ascend)
- [openGemini/openGemini](https://github.com/openGemini/openGemini)
- [sermant-io/Sermant](https://github.com/sermant-io/Sermant)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [istio/istio](https://github.com/istio/istio)
