# Solo.io 云原生开源案例（初稿）

## 关键观察

- Solo.io 在 `Istio` 社区中长期深度参与，并有 maintainer 级别贡献者。
- `Gloo` 体系已演进为 `kgateway`，是其 API Gateway / AI Gateway 方向的核心项目。
- 在 Agent 方向，围绕 `kagent` 延伸出 `Agent Registry`、`Agent Gateway`、`agentevals` 等能力。

## 可编辑开源全景图（Mermaid）

```mermaid
flowchart TB
  subgraph MESH["上游参与与服务网格层"]
    ISTIO["⭐ Istio<br/>Maintainer-Level Participation"]
  end

  subgraph GATEWAY["网关与流量治理层"]
    KGW["⭐ kgateway（原 Gloo）<br/>Cloud-Native API / AI Gateway"]
    AGW["Agent Gateway<br/>Agent 请求入口 / 路由治理"]
  end

  subgraph AGENT["Agent 运行与评测层"]
    KAG["⭐ kagent<br/>Cloud Native Agentic AI"]
    REG["Agent Registry<br/>Agent/Tool 注册与发现"]
    AEV["agentevals<br/>Agent Evaluations (OTel Traces)"]
  end

  subgraph CORE["统一控制平面"]
    K8S["Kubernetes"]
  end

  ISTIO --> K8S
  KGW --> K8S
  KAG --> K8S

  AGW --> KGW
  AGW --> KAG
  REG --> KAG
  KAG --> AEV

  KGW -. mesh integration .-> ISTIO

  classDef star fill:#fff2e6,stroke:#d97706,color:#7c2d12,stroke-width:1.2px;
  classDef normal fill:#eaf2ff,stroke:#4f81bd,color:#1b2a41,stroke-width:1px;
  classDef core fill:#e8fff1,stroke:#16a34a,color:#14532d,stroke-width:1.3px;

  class ISTIO,KGW,KAG star;
  class AGW,REG,AEV normal;
  class K8S core;
```

## 发起/主导项目（代表）

- [kgateway-dev/kgateway](https://github.com/kgateway-dev/kgateway)（Gloo 演进 / 更名方向）
- [solo-io/gloo](https://github.com/solo-io/gloo)（历史主线项目）
- [kagent-dev/kagent](https://github.com/kagent-dev/kagent)
- [agentevals-dev/agentevals](https://github.com/agentevals-dev/agentevals)
- [kagent-dev/kmcp](https://github.com/kagent-dev/kmcp)（Agent 工具协议与连接能力）
- [kagent-dev/tools](https://github.com/kagent-dev/tools)（Agent 工具生态）

## 深度参与项目（代表）

- [istio/istio](https://github.com/istio/istio)
- [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes)
- [kubernetes-sigs/gateway-api](https://github.com/kubernetes-sigs/gateway-api)
