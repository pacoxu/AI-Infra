# 蚂蚁集团（Ant Group）云原生开源案例（初稿）

## 可编辑全景图（Mermaid）

```mermaid
flowchart TB
  ANT["蚂蚁开源全景图"]

  subgraph DIST["分发与镜像"]
    DFLY["Dragonfly"]
    NYD["Nydus"]
    HARBOR["Harbor"]
  end

  subgraph PLATFORM["平台工程与运维（KusionStack）"]
    KS["KusionStack 社区"]
    KCL["KCL"]
    KARPOR["Karpor"]
    CMESH["Controller Mesh"]
    KUP["Kuperator"]
  end

  subgraph AI["模型与 AI 交付"]
    MPORG["modelpack（GitHub Org）"]
    MPC["modelpack/community"]
  end

  subgraph RUNTIME["运行时与安全隔离"]
    KATA["Kata Containers"]
  end

  subgraph UPSTREAM["上游生态参与"]
    K8S["Kubernetes（参与）"]
  end

  subgraph ECO["生态协作（补充提及）"]
    ARGO["Argo"]
    FLANNEL["flannel"]
  end

  ANT --> DFLY
  ANT --> NYD
  ANT --> HARBOR
  ANT --> KS
  ANT --> KCL
  ANT --> MPORG
  ANT --> KATA
  ANT --> K8S
  ANT --> ARGO
  ANT --> FLANNEL

  KS --> KCL
  KS --> KARPOR
  KS --> CMESH
  KS --> KUP
  MPORG --> MPC

  DFLY --> K8S
  NYD --> K8S
  NYD -. image format / lazy pull .-> DFLY
  HARBOR --> K8S
  KATA --> K8S
  KUP --> K8S
  ARGO --> K8S
  FLANNEL --> K8S
```

## 发起/主导项目（代表）

- [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly)
- [goharbor/harbor](https://github.com/goharbor/harbor)
- [KusionStack/community](https://github.com/KusionStack/community)（KusionStack 社区入口）
- [KusionStack/karpor](https://github.com/KusionStack/karpor)
- [KusionStack/controller-mesh](https://github.com/KusionStack/controller-mesh)
- [KusionStack/kuperator](https://github.com/KusionStack/kuperator)
- [modelpack（GitHub Org）](https://github.com/modelpack/)
- [modelpack/community](https://github.com/modelpack/community)
- [kata-containers/kata-containers](https://github.com/kata-containers/kata-containers)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)

## 补充提及（基于全景图）

- [kcl-lang/kcl](https://github.com/kcl-lang/kcl)
- [dragonflyoss/nydus](https://github.com/dragonflyoss/nydus)
- [argoproj/argo-workflows](https://github.com/argoproj/argo-workflows)
- [flannel-io/flannel](https://github.com/flannel-io/flannel)
