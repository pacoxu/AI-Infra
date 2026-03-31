# DaoCloud 云原生开源案例（初稿）

## 参考输入

- DaoCloud Profile README: https://github.com/DaoCloud/.github/blob/main/profile/README.md

## 可编辑生态图（Mermaid）

```mermaid
flowchart LR
  D["DaoCloud / d.run 开源生态"]

  subgraph FOUNDED["发起/共建项目"]
    SP["⭐ Spiderpool"]
    CP["⭐ Clusterpedia"]
    KA["⭐ kubean"]
    HM["⭐ HAMi"]
    HW["Hwameistor"]
    LMD["llm-d"]
    KW["knoway"]
    MB["merbridge"]
  end

  subgraph MAINT["深度参与/维护项目"]
    K8S["⭐ Kubernetes"]
    VLLM["⭐ vLLM"]
    CTD["containerd"]
    KUEUE["kueue"]
    KWOK["kwok"]
    LWS["lws"]
    KSP["kubespray"]
    KADM["kubeadm"]
    ISTIO["Istio"]
  end

  D --> SP
  D --> CP
  D --> KA
  D --> HM
  D --> HW
  D --> LMD
  D --> KW
  D --> MB
  D --> K8S
  D --> VLLM
  D --> CTD
  D --> KUEUE
  D --> KWOK
  D --> LWS
  D --> KSP
  D --> KADM
  D --> ISTIO

  SP --> K8S
  CP --> K8S
  KA --> KSP
  KA --> K8S
  HM --> K8S
  CTD --> K8S
  KUEUE --> K8S
  KWOK --> K8S
  LWS --> K8S
  KADM --> K8S
  LMD --> K8S
  LMD --> VLLM

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;

  class SP,CP,KA,HM,K8S,VLLM star;
  class HW,LMD,KW,MB,CTD,KUEUE,KWOK,LWS,KSP,KADM,ISTIO normal;
```

## 发起/主导项目（代表）

- [⭐ spidernet-io/spiderpool](https://github.com/spidernet-io/spiderpool)
- [⭐ clusterpedia-io/clusterpedia](https://github.com/clusterpedia-io/clusterpedia)
- [⭐ kubean-io/kubean](https://github.com/kubean-io/kubean)
- [⭐ Project-HAMi/HAMi](https://github.com/Project-HAMi/HAMi)
- [knoway-dev/knoway](https://github.com/knoway-dev/knoway)
- [merbridge/merbridge](https://github.com/merbridge/merbridge)
- [hwameistor/hwameistor](https://github.com/hwameistor/hwameistor)
- [llm-d/llm-d](https://github.com/llm-d/llm-d)
- [kdoctor-io/kdoctor](https://github.com/kdoctor-io/kdoctor)

## 深度参与项目（代表）

- [⭐ kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [⭐ vllm-project/vllm](https://github.com/vllm-project/vllm)
- [containerd/containerd](https://github.com/containerd/containerd)
- [kubernetes-sigs/kueue](https://github.com/kubernetes-sigs/kueue)
- [kubernetes-sigs/kwok](https://github.com/kubernetes-sigs/kwok)
- [kubernetes-sigs/lws](https://github.com/kubernetes-sigs/lws)
- [kubernetes-sigs/kubespray](https://github.com/kubernetes-sigs/kubespray)
- [kubernetes/kubeadm](https://github.com/kubernetes/kubeadm)
- [istio/istio](https://github.com/istio/istio)
