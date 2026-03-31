# 阿里巴巴（Alibaba）云原生开源案例（初稿）

## 重点整理

- `Higress`：新晋 CNCF Sandbox（API Gateway 方向）
- `Kata Containers`：容器隔离与安全运行时领域的重要项目

## 可编辑架构分层图（Mermaid）

```mermaid
flowchart TB
  subgraph L1["L1 入口与应用交付层"]
    HIG["⭐ Higress<br/>（CNCF Sandbox）"]
    KVL["KubeVela"]
    OKR["OpenKruise"]
    OY["OpenYurt"]
  end

  subgraph L2["L2 调度与资源管理层"]
    KRD["⭐ Koordinator"]
  end

  subgraph L3["L3 运行时与安全层"]
    KATA["⭐ Kata Containers"]
    COC["Confidential Containers"]
    CB["ChaosBlade"]
  end

  subgraph L4["L4 数据与分发加速层"]
    FLUID["Fluid"]
    DFLY["Dragonfly"]
  end

  subgraph L5["L5 中间件与治理层"]
    NACOS["Nacos"]
    SENT["Sentinel"]
  end

  subgraph BASE["基础开源底座（深度参与）"]
    K8S["Kubernetes"]
    ISTIO["Istio"]
  end

  HIG --> KRD
  KVL --> OKR
  OKR --> KRD
  OY --> K8S
  KRD --> OKR
  KRD --> K8S
  KATA --> K8S
  COC --> KATA
  CB --> K8S
  FLUID --> K8S
  DFLY --> FLUID
  NACOS --> K8S
  SENT --> K8S
  HIG --> ISTIO
  ISTIO --> K8S

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;

  class HIG,KRD,KATA star;
  class KVL,OKR,OY,COC,CB,FLUID,DFLY,NACOS,SENT,K8S,ISTIO normal;
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
