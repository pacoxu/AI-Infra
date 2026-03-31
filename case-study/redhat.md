# Red Hat 云原生开源案例（初稿）

## 可编辑开源全景图（Mermaid）

```mermaid
flowchart TB
  subgraph PLATFORM["企业发行版与平台层（Red Hat 血统）"]
    K8S["Kubernetes（联合发起/早期核心贡献）"]
    OKD["OKD"]
    OCP["OpenShift"]
  end

  subgraph MULTI["多集群与运维控制面"]
    OCM["Open Cluster Management"]
    OF["Operator Framework"]
    SDK["Operator SDK"]
    OLM["Operator Lifecycle Manager"]
    OH["OperatorHub"]
  end

  subgraph RUNTIME["虚拟化与运行时层"]
    KV["KubeVirt"]
    CRIO["CRI-O"]
    KEDA["KEDA"]
  end

  subgraph MODERNIZE["迁移与基础设施"]
    KONV["Konveyor"]
    M3["Metal3.io"]
  end

  subgraph UPSTREAM["深度参与生态（非 Red Hat 主导）"]
    ETCD["etcd"]
    KN["Knative"]
    ISTIO["Istio"]
    ARGO["Argo"]
    PROM["Prometheus"]
    JAE["Jaeger"]
  end

  OKD --> OCP
  K8S --> OCP
  OCP --> OCM
  OCP --> OF
  OCP --> KV
  OCP --> CRIO
  OCP --> KEDA
  OCP --> KONV
  OCP --> M3

  OF --> SDK
  OF --> OLM
  OF --> OH

  OCP -. ecosystem integration .-> ETCD
  OCP -. ecosystem integration .-> KN
  OCP -. ecosystem integration .-> ISTIO
  OCP -. ecosystem integration .-> ARGO
  OCP -. ecosystem integration .-> PROM
  OCP -. ecosystem integration .-> JAE

  classDef core fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;

  class K8S,OKD,OCP,OCM,OF,KV,CRIO,KEDA core;
  class SDK,OLM,OH,KONV,M3,ETCD,KN,ISTIO,ARGO,PROM,JAE normal;
```

## 发起/主导项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)（历史联合发起/早期核心贡献）
- [openshift/origin](https://github.com/openshift/origin)
- [open-cluster-management-io/ocm](https://github.com/open-cluster-management-io/ocm)（Open Cluster Management）
- [operator-framework/operator-sdk](https://github.com/operator-framework/operator-sdk)
- [operator-framework/operator-lifecycle-manager](https://github.com/operator-framework/operator-lifecycle-manager)
- [operatorhub.io](https://operatorhub.io/)（OperatorHub 生态入口）
- [kubevirt/kubevirt](https://github.com/kubevirt/kubevirt)
- [cri-o/cri-o](https://github.com/cri-o/cri-o)
- [kedacore/keda](https://github.com/kedacore/keda)

## 发起/主导（或 Red Hat 血统很强）

- [okd-project/okd](https://github.com/okd-project/okd) / [openshift/origin](https://github.com/openshift/origin)（OKD / OpenShift upstream）
- [open-cluster-management-io/ocm](https://github.com/open-cluster-management-io/ocm)（Open Cluster Management）
- Operator Framework：  
  [operator-framework/operator-sdk](https://github.com/operator-framework/operator-sdk) /  
  [operator-framework/operator-lifecycle-manager](https://github.com/operator-framework/operator-lifecycle-manager) /  
  [operatorhub.io](https://operatorhub.io/)
- [kubevirt/kubevirt](https://github.com/kubevirt/kubevirt)
- [cri-o/cri-o](https://github.com/cri-o/cri-o)
- [kedacore/keda](https://github.com/kedacore/keda)
- [konveyor（GitHub Org）](https://github.com/konveyor)
- [metal3-io（GitHub Org）](https://github.com/metal3-io)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [etcd-io/etcd](https://github.com/etcd-io/etcd)
- [knative/serving](https://github.com/knative/serving)
- [istio/istio](https://github.com/istio/istio)
- [argoproj/argo-workflows](https://github.com/argoproj/argo-workflows)
- [prometheus/prometheus](https://github.com/prometheus/prometheus)
- [jaegertracing/jaeger](https://github.com/jaegertracing/jaeger)
