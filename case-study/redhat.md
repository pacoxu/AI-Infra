# Red Hat 云原生开源案例（初稿）

## 可编辑开源全景图（Mermaid）

```mermaid
flowchart LR
  subgraph BASE["基础底座 / Upstream Foundation"]
    K8S["Kubernetes\n（非 Red Hat 发起；长期核心贡献）"]
  end

  subgraph PLATFORM["平台发行版 / Red Hat 血统"]
    OKD["OKD\n（OpenShift upstream）"]
    OCP["OpenShift\n（企业发行版 / 产品映射）"]
  end

  subgraph CONTROL["集群控制面与平台扩展"]
    OCM["Open Cluster Management"]
    OF["Operator Framework"]
    SDK["Operator SDK"]
    OLM["OLM"]
    OH["OperatorHub"]
  end

  subgraph WORKLOAD["工作负载能力"]
    KV["KubeVirt"]
    CRIO["CRI-O\n（Red Hat 发起）"]
    KEDA["KEDA\n（与 Microsoft 共同创建）"]
  end

  subgraph INFRA["现代化 / 基础设施"]
    KONV["Konveyor"]
    M3["Metal3.io"]
  end

  subgraph ECO["生态集成 / 深度参与（非 Red Hat 主导）"]
    ETCD["etcd"]
    KN["Knative"]
    KSERVE["KServe"]
    LLMD["llm-d"]
    VLLM["vLLM"]
    ISTIO["Istio"]
    ARGO["Argo"]
    PROM["Prometheus"]
    JAE["Jaeger"]
  end

  K8S --> OKD
  OKD --> OCP

  K8S --> OF
  OF --> SDK
  OF --> OLM
  OLM --> OH
  OCP --> OCM

  K8S --> KV
  K8S --> CRIO
  K8S --> KEDA
  OCP --> KONV
  K8S --> M3

  K8S -. control-plane storage .-> ETCD
  OCP -. ecosystem integration .-> KN
  OCP -. model serving integration .-> KSERVE
  OCP -. disaggregated inference orchestration .-> LLMD
  OCP -. inference engine ecosystem .-> VLLM
  OCP -. service mesh integration .-> ISTIO
  OCP -. GitOps / delivery .-> ARGO
  OCP -. observability .-> PROM
  OCP -. tracing .-> JAE
  KSERVE -. builds on .-> KN
  KSERVE -. commonly serves .-> VLLM
  LLMD -. runs on .-> K8S
  LLMD -. can orchestrate .-> VLLM

  classDef rh fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.4px;
  classDef eco fill:#eef4ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef prod fill:#f5f5f5,stroke:#666,color:#222,stroke-dasharray: 5 3;

  class OKD,OCM,OF,SDK,OLM,OH,KV,CRIO,KEDA,KONV,M3 rh;
  class ETCD,K8S,KN,KSERVE,LLMD,VLLM,ISTIO,ARGO,PROM,JAE eco;
  class OCP prod;
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
- [kedacore/keda](https://github.com/kedacore/keda)（与 Microsoft 共同创建）

## 发起/主导（或 Red Hat 血统很强）

- [okd-project/okd](https://github.com/okd-project/okd) / [openshift/origin](https://github.com/openshift/origin)（OKD / OpenShift upstream）
- [open-cluster-management-io/ocm](https://github.com/open-cluster-management-io/ocm)（Open Cluster Management）
- Operator Framework：  
  [operator-framework/operator-sdk](https://github.com/operator-framework/operator-sdk) /  
  [operator-framework/operator-lifecycle-manager](https://github.com/operator-framework/operator-lifecycle-manager) /  
  [operatorhub.io](https://operatorhub.io/)
- [kubevirt/kubevirt](https://github.com/kubevirt/kubevirt)
- [cri-o/cri-o](https://github.com/cri-o/cri-o)
- [kedacore/keda](https://github.com/kedacore/keda)（与 Microsoft 共同创建）
- [konveyor（GitHub Org）](https://github.com/konveyor)
- [metal3-io（GitHub Org）](https://github.com/metal3-io)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [etcd-io/etcd](https://github.com/etcd-io/etcd)
- [knative/serving](https://github.com/knative/serving)
- [kserve/kserve](https://github.com/kserve/kserve)
- [llm-d/llm-d](https://github.com/llm-d/llm-d)
- [vllm-project/vllm](https://github.com/vllm-project/vllm)
- [istio/istio](https://github.com/istio/istio)
- [argoproj/argo-workflows](https://github.com/argoproj/argo-workflows)
- [prometheus/prometheus](https://github.com/prometheus/prometheus)
- [jaegertracing/jaeger](https://github.com/jaegertracing/jaeger)
