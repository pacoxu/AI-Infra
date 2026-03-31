# 阿里巴巴（Alibaba）云原生开源案例（初稿）

## 重点整理

- `Higress`：新晋 CNCF Sandbox（API Gateway 方向）
- `Kata Containers`：容器隔离与安全运行时领域的重要项目

## 可编辑生态图（Mermaid）

```mermaid
flowchart LR
  ALI["Alibaba 云原生开源生态"]

  subgraph APP["应用平台与入口治理"]
    HIG["⭐ Higress<br/>（CNCF Sandbox）"]
    OKR["OpenKruise"]
    KVL["KubeVela"]
    OY["OpenYurt"]
  end

  subgraph SCH["调度与资源管理"]
    KRD["⭐ Koordinator"]
  end

  subgraph RTSEC["运行时与机密计算/安全"]
    KATA["⭐ Kata Containers"]
    COC["Confidential Containers"]
    CB["ChaosBlade"]
  end

  subgraph DATA["数据与加速"]
    FLUID["Fluid"]
    DFLY["Dragonfly"]
  end

  subgraph MIDDLE["中间件与治理"]
    NACOS["Nacos"]
    SENT["Sentinel"]
  end

  ALI --> HIG
  ALI --> OKR
  ALI --> KVL
  ALI --> OY
  ALI --> KRD
  ALI --> KATA
  ALI --> COC
  ALI --> CB
  ALI --> FLUID
  ALI --> DFLY
  ALI --> NACOS
  ALI --> SENT

  KRD --> OKR
  KATA --> COC
  HIG --> KVL
  FLUID --> KRD
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
