# Azure（Microsoft）云原生开源案例（初稿）

## 可编辑开源全景图（Mermaid）

```mermaid
flowchart TB
  subgraph APP["应用抽象与开发体验层"]
    DAPR["⭐ Dapr<br/>Distributed Application Runtime"]
    KVL["KubeVela<br/>Application Delivery Abstraction"]
    KAITO["⭐ Kaito<br/>AI Operator / LLM on Kubernetes"]
  end

  subgraph CTRL["控制面与平台扩展层"]
    FLEET["⭐ Azure Fleet<br/>Multi-Cluster Orchestration"]
    VK["Virtual Kubelet<br/>Virtual Node Extension"]
    ASO["Azure Service Operator<br/>Manage Azure Resources via CRDs"]
    KEDA["⭐ KEDA<br/>Event-Driven Autoscaling"]
    OSM["Open Service Mesh (OSM)"]
  end

  subgraph CORE["统一控制平面"]
    K8S["Kubernetes"]
  end

  subgraph BASE["运行时与策略基座"]
    CTD["containerd"]
    ETCD["etcd"]
    OPA["Open Policy Agent"]
  end

  subgraph ECO["生态深度参与"]
    ISTIO["Istio"]
    HEAD["Headlamp"]
    SR["Semantic Router"]
  end

  DAPR --> K8S
  KVL --> K8S
  KAITO --> K8S

  FLEET --> K8S
  VK --> K8S
  ASO --> K8S
  KEDA --> K8S
  OSM --> K8S

  K8S --> CTD
  K8S --> ETCD
  OPA --> K8S

  DAPR -. often coupled with .-> KEDA
  OSM -. service mesh ecosystem .-> ISTIO
  KAITO -. AI workload scaling can integrate with .-> KEDA
  HEAD --> K8S
  SR --> KAITO
  SR -. semantic routing for AI traffic .-> K8S

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef core fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.3px;
  classDef base fill:#f5f5f5,stroke:#666,color:#222,stroke-width:1px;

  class DAPR,FLEET,KEDA,KAITO star;
  class KVL,VK,ASO,OSM,ISTIO,HEAD,SR normal;
  class K8S core;
  class CTD,ETCD,OPA base;
```

## 发起/共同发起项目（代表）

- [dapr/dapr](https://github.com/dapr/dapr)
- [kedacore/keda](https://github.com/kedacore/keda)
- [virtual-kubelet/virtual-kubelet](https://github.com/virtual-kubelet/virtual-kubelet)
- [openservicemesh/osm](https://github.com/openservicemesh/osm)
- [Azure/azure-service-operator](https://github.com/Azure/azure-service-operator)
- [kubevela/kubevela](https://github.com/kubevela/kubevela)
- [Azure/fleet](https://github.com/Azure/fleet)
- [kaito-project/kaito](https://github.com/kaito-project/kaito)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [istio/istio](https://github.com/istio/istio)
- [containerd/containerd](https://github.com/containerd/containerd)
- [etcd-io/etcd](https://github.com/etcd-io/etcd)
- [open-policy-agent/opa](https://github.com/open-policy-agent/opa)
- [kubernetes-sigs/headlamp](https://github.com/kubernetes-sigs/headlamp)
- [vllm-project/semantic-router](https://github.com/vllm-project/semantic-router)
