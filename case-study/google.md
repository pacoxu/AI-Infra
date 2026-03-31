# Google 云原生开源案例（全景版）

## 参考输入

- 你提供的图片（Consistent Consumption & Operational Model）

## 可编辑开源全景图（Mermaid）

```mermaid
flowchart TB
  subgraph USER["用户与应用团队"]
    U1["Team A"]
    U2["Team B"]
    U3["Team C"]
  end

  subgraph API["统一消费与操作模型（API - General）"]
    K8S["⭐ Kubernetes"]
    KUEUE["Kueue"]
    KUBEFLOW["Kubeflow"]
    SLURM["Slurm"]
    RAY["Ray"]
    MORE["..."]
  end

  subgraph CONTROL["控制与交付平面"]
    KNATIVE["Knative"]
    TEKTON["Tekton"]
    BAZEL["Bazel"]
  end

  subgraph POOL["多集群/计算池层（同一模型跨集群复用）"]
    P1["Compute Pool #1"]
    P2["Compute Pool #2"]
    P3["Compute Pool #3"]
  end

  subgraph NODE["节点运行时与可观测"]
    CTD["containerd"]
    GVISOR["gVisor"]
    CADV["cAdvisor"]
    GPU["NVIDIA GPU Nodes"]
  end

  subgraph GOVERN["服务治理与流量"]
    ISTIO["Istio"]
  end

  subgraph STORAGE["状态与元数据"]
    ETCD["etcd"]
  end

  U1 --> API
  U2 --> API
  U3 --> API

  K8S --> P1
  K8S --> P2
  K8S --> P3
  KUEUE --> K8S
  KUBEFLOW --> K8S
  SLURM -. workload integration .-> K8S
  RAY -. workload integration .-> K8S

  KNATIVE --> K8S
  TEKTON --> K8S
  BAZEL --> TEKTON

  P1 --> CTD
  P2 --> CTD
  P3 --> CTD
  CTD --> GVISOR
  CTD --> CADV
  P1 --> GPU
  P2 --> GPU
  P3 --> GPU

  ISTIO --> K8S
  ETCD --> K8S

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef base fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.2px;

  class K8S,KUEUE,KUBEFLOW,KNATIVE,TEKTON,BAZEL,GVISOR,CADV,ISTIO star;
  class SLURM,RAY,MORE,P1,P2,P3,CTD,GPU,ETCD normal;
  class U1,U2,U3 base;
```

## 发起/共同发起项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [istio/istio](https://github.com/istio/istio)
- [knative/serving](https://github.com/knative/serving)
- [google/gvisor](https://github.com/google/gvisor)
- [google/cadvisor](https://github.com/google/cadvisor)
- [bazelbuild/bazel](https://github.com/bazelbuild/bazel)
- [tektoncd/pipeline](https://github.com/tektoncd/pipeline)
- [kubeflow/kubeflow](https://github.com/kubeflow/kubeflow)
- [kubernetes-sigs/kueue](https://github.com/kubernetes-sigs/kueue)
- [ray-project/ray](https://github.com/ray-project/ray)

## 深度参与项目（代表）

- [containerd/containerd](https://github.com/containerd/containerd)
- [etcd-io/etcd](https://github.com/etcd-io/etcd)
- [SchedMD/slurm](https://github.com/SchedMD/slurm)
