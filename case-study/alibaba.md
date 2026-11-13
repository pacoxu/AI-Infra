# 阿里巴巴（Alibaba）云原生开源案例（全景版）

## 一句话结论

阿里云原生开源横跨 **网关（Higress）、应用交付（KubeVela / OpenKruise）、混部调度（Koordinator）、边缘（OpenYurt）、安全运行时（Kata）与数据分发（Fluid / Dragonfly）**；AI 侧以 SGLang / RBG 补齐推理引擎与批路由。

## 重点整理

- `Higress`：CNCF Sandbox（API / AI Gateway）
- `Kata Containers`：轻量 VM 安全运行时
- `SGLang / RBG`：LLM Serving 与请求批处理 / 路由

## 可编辑架构分层图（Mermaid）

```mermaid
flowchart TB
  subgraph ENTRY["入口与应用交付面"]
    HIG["⭐ Higress<br/>AI / API Gateway"]
    KVL["KubeVela<br/>Application Delivery Control Plane"]
  end

  subgraph AI["AI 推理与请求路由面"]
    SGL["SGLang<br/>LLM Serving Engine"]
    RBG["RBG<br/>Request Batching / Routing Gateway"]
  end

  subgraph CTRL["工作负载与资源控制面"]
    OKR["OpenKruise<br/>Workload Automation"]
    KRD["⭐ Koordinator<br/>Scheduling / QoS / Colocation"]
    OY["OpenYurt<br/>Edge Extension"]
  end

  subgraph GOV["服务发现与流量治理面"]
    ISTIO["Istio"]
    NACOS["Nacos"]
    SENT["Sentinel"]
  end

  K8S["⭐ Kubernetes<br/>统一控制平面"]

  subgraph RUNTIME["运行时与安全面（位于 Kubernetes 下方）"]
    KATA["⭐ Kata Containers<br/>Lightweight VM Runtime"]
    COC["Confidential Containers"]
    CB["ChaosBlade"]
  end

  subgraph DATA["数据分发与缓存加速面（位于 Kubernetes 下方）"]
    FLUID["Fluid<br/>Dataset / Cache Orchestration"]
    DFLY["Dragonfly<br/>P2P Distribution Acceleration"]
  end

  %% stronger relationships
  KVL --> K8S
  OKR --> K8S
  KRD --> K8S
  OY --> K8S
  K8S --> KATA
  K8S --> FLUID
  ISTIO --> K8S
  HIG --> ISTIO
  HIG --> RBG
  RBG --> SGL
  SGL --> K8S

  %% collaboration / ecosystem integrations
  KVL -. often drives .-> OKR
  KRD -. works with workload scheduling .-> OKR
  OY -. extends Kubernetes to edge .-> K8S
  COC -. commonly builds on Kata ecosystem .-> KATA
  K8S -. chaos engineering with .-> CB
  K8S -. accelerates images / OCI / models / files via .-> DFLY
  DFLY -. can complement caching / distribution .-> FLUID
  NACOS -. service discovery / config for workloads on .-> K8S
  SENT -. traffic governance / resilience for workloads on .-> K8S
  SENT -. complements .-> ISTIO
  NACOS -. can integrate with gateways / services .-> HIG

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef base fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.3px;

  class HIG,KRD,KATA,K8S star;
  class KVL,OKR,OY,COC,CB,FLUID,DFLY,NACOS,SENT,ISTIO,SGL,RBG normal;
```

## 发起/主导项目（代表）

- [higress-group/higress](https://github.com/higress-group/higress)
- [openyurtio/openyurt](https://github.com/openyurtio/openyurt)
- [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers)
- [koordinator-sh/koordinator](https://github.com/koordinator-sh/koordinator)
- [chaosblade-io/chaosblade](https://github.com/chaosblade-io/chaosblade)
- [confidential-containers/confidential-containers](https://github.com/confidential-containers/confidential-containers)
- [openkruise/kruise](https://github.com/openkruise/kruise)
- [kubevela/kubevela](https://github.com/kubevela/kubevela)
- [fluid-cloudnative/fluid](https://github.com/fluid-cloudnative/fluid)
- [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly)
- [alibaba/nacos](https://github.com/alibaba/nacos)
- [alibaba/Sentinel](https://github.com/alibaba/Sentinel)

## 补充：AI 推理生态项目（本图纳入）

- [sgl-project/sglang](https://github.com/sgl-project/sglang)
- [sgl-project/rbg](https://github.com/sgl-project/rbg)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [istio/istio](https://github.com/istio/istio)
