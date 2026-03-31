# Google 云原生开源案例（初稿）

## 可编辑开源全景图（Mermaid）

```mermaid
flowchart TB
  subgraph APP["应用与流量治理层"]
    ISTIO["⭐ Istio"]
    KN["⭐ Knative"]
  end

  subgraph AIJOB["AI / 批处理编排层"]
    KUEUE["Kueue"]
    DRANET["DRANET"]
    KFB["Kubeflow"]
  end

  subgraph DEVOPS["构建与交付层"]
    BZL["Bazel"]
    TEK["Tekton Pipeline"]
  end

  subgraph CORE["Kubernetes 核心基座"]
    K8S["⭐ Kubernetes"]
    CTD["containerd"]
    ETCD["etcd"]
  end

  subgraph NODE["节点运行时与可观测"]
    GVS["gVisor"]
    CADV["cAdvisor"]
  end

  ISTIO --> K8S
  KN --> K8S
  KUEUE --> K8S
  DRANET --> K8S
  KFB --> K8S

  BZL --> TEK
  TEK --> K8S

  K8S --> CTD
  K8S --> ETCD
  GVS --> CTD
  CADV --> K8S

  KUEUE -. queue / quota for AI jobs .-> KFB
  DRANET -. DRA-based high-perf networking .-> KUEUE

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef base fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.2px;

  class K8S,ISTIO,KN star;
  class KUEUE,DRANET,KFB,BZL,TEK,GVS,CADV normal;
  class CTD,ETCD base;
```

## 发起/共同发起项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [istio/istio](https://github.com/istio/istio)
- [knative/serving](https://github.com/knative/serving)
- [google/gvisor](https://github.com/google/gvisor)
- [google/cadvisor](https://github.com/google/cadvisor)
- [bazelbuild/bazel](https://github.com/bazelbuild/bazel)
- [tektoncd/pipeline](https://github.com/tektoncd/pipeline)

## 深度参与项目（代表）

- [containerd/containerd](https://github.com/containerd/containerd)
- [etcd-io/etcd](https://github.com/etcd-io/etcd)

## 补充：Google 生态重点项目（可纳入全景图）

- [kubernetes-sigs/kueue](https://github.com/kubernetes-sigs/kueue)
- [google/dranet](https://github.com/google/dranet)
- [kubernetes-sigs/dranet](https://github.com/kubernetes-sigs/dranet)
- [kubeflow/kubeflow](https://github.com/kubeflow/kubeflow)
