# 字节跳动（ByteDance）云原生开源案例（初稿）

## 参考输入

- 你提供的文章链接：https://mp.weixin.qq.com/s/fUK6qqcFzkoNcscHBE9v8A
- 你提供的分层图（KubeBrain / Godel / Katalyst / kubeadmiral / podseidon / kelemetry 等）

## 分层视角（基于你给的图和字节方案）

- 多集群与联邦层：`kubeadmiral`、`podseidon`
- 入口与治理层：`kubegateway`、`kubezoo`
- 核心控制面层：`kubebrain`（元信息存储）、`godel-scheduler`（调度）
- 节点与数据面层：`katalyst-core`
- 跨层可观测层：`kelemetry`

## 可编辑架构图（Mermaid）

```mermaid
flowchart TB
  subgraph L1["Multi-Cluster & Federation Layer (多集群与联邦层)"]
    KA["6. kubeadmiral<br/>多集群编排"]
    PS["7. podseidon<br/>多集群保护"]
  end

  subgraph L2["Access & Governance Layer (入口与治理层)"]
    KGW["2. KubeGateway<br/>七层网关（L7入口）"]
    KZZ["3. KubeZoo<br/>轻量级多租户（租户隔离）"]
  end

  subgraph L3["Core Control Plane Layer (核心控制面层)"]
    subgraph API["API & Logic"]
      KAS["kube-apiserver"]
      KCM["kube-controller-manager"]
    end

    subgraph SCH["Scheduling (调度)"]
      KSCH["kube-scheduler<br/>（标准调度）"]
      GODEL["4. Godel Scheduler<br/>（大规模混部调度）"]
    end

    subgraph STO["Storage (存储)"]
      KB["1. KubeBrain<br/>（高性能元信息存储，替代 etcd）"]
      TIKV["TiKV<br/>（社区版本）"]
      BKV["ByteKV<br/>（内部）"]
    end
  end

  subgraph L4["Node & Data Plane Layer (节点与数据面层)"]
    KLET["kubelet"]
    KAT["5. ⭐ Katalyst<br/>（kubelet 增强：节点资源管理/拓扑感知）"]
  end

  subgraph L5["Observability Layer (可观测性层 - 跨层级)"]
    KEL["8. kelemetry<br/>（定时拉取信息 / 也可上报信息）"]
  end

  KA --> KGW
  KA --> KZZ
  PS -. 保护多集群 .-> KA
  KGW --> KAS
  KZZ --> KAS
  KCM --> KAS
  KSCH --> KAS
  GODEL --> KAS
  KAS --> KB
  KB --> TIKV
  KB --> BKV
  KAS --> KLET
  KLET --> KAT

  classDef std fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef bt fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef backend fill:#f5f5f5,stroke:#666,color:#333,stroke-width:1px;

  class KAS,KCM,KSCH,KLET std;
  class KA,PS,KGW,KZZ,GODEL,KB,KAT,KEL bt;
  class TIKV,BKV backend;
```

## 发起/主导项目（代表）

- [kubewharf/kubebrain](https://github.com/kubewharf/kubebrain)
- [kubewharf/godel-scheduler](https://github.com/kubewharf/godel-scheduler)
- [kubewharf/katalyst-core](https://github.com/kubewharf/katalyst-core)
- [kubewharf/kubeadmiral](https://github.com/kubewharf/kubeadmiral)
- [kubewharf/podseidon](https://github.com/kubewharf/podseidon)
- [kubewharf/kubegateway](https://github.com/kubewharf/kubegateway)
- [kubewharf/kubezoo](https://github.com/kubewharf/kubezoo)
- [kubewharf/kelemetry](https://github.com/kubewharf/kelemetry)

## 深度参与项目（代表）

- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [istio/istio](https://github.com/istio/istio)
- [etcd-io/etcd](https://github.com/etcd-io/etcd)
