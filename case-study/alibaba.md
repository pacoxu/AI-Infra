# 阿里巴巴（Alibaba）云原生开源案例（初稿）

## 重点整理

- `Higress`：新晋 CNCF Sandbox（API Gateway 方向）
- `Kata Containers`：容器隔离与安全运行时领域的重要项目

## 可编辑架构分层图（Mermaid）

```mermaid
flowchart TB
  subgraph ENTRY["入口与应用交付面"]
    HIG["⭐ Higress<br/>AI / API Gateway"]
    KVL["KubeVela<br/>Application Delivery Control Plane"]
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
  class KVL,OKR,OY,COC,CB,FLUID,DFLY,NACOS,SENT,ISTIO normal;
```

## 发起/主导项目（代表）

- [alibaba/higress](https://github.com/alibaba/higress)
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

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [istio/istio](https://github.com/istio/istio)
