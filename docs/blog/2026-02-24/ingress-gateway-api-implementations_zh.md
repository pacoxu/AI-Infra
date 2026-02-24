---
status: Active
maintainer: pacoxu
last_updated: 2026-02-24
tags: kubernetes, ingress, gateway-api, networking, ai-gateway, gaie
---

# Ingress 到 Gateway API：Kubernetes 入口控制器实现全景评测

**注意：** 部分内容由 AI 辅助生成，请在生产环境使用前仔细验证。所有 conformance
状态及活跃度数据均以 2026-02-24 为基准时间采集。

## 目录

- [背景：为什么现在是关键节点](#背景为什么现在是关键节点)
- [Gateway API 标准](#gateway-api-标准)
- [Gateway API 推理扩展（GAIE）](#gateway-api-推理扩展gaie)
- [实现方案逐一评测](#实现方案逐一评测)
  - [Envoy Gateway](#envoy-gateway)
  - [NGINX Gateway Fabric](#nginx-gateway-fabric)
  - [Traefik](#traefik)
  - [kgateway（前身 Gloo）](#kgateway前身-gloo)
  - [Cilium](#cilium)
  - [Istio](#istio)
  - [Contour](#contour)
  - [Higress](#higress)
  - [HAProxy Ingress](#haproxy-ingress)
  - [Kong Ingress Controller](#kong-ingress-controller)
- [场景化选型指南](#场景化选型指南)
- [汇总对比表](#汇总对比表)
- [参考资料](#参考资料)

## 背景：为什么现在是关键节点

Kubernetes 入口控制器生态正处于一个明显的换档期。**Ingress NGINX** 作为部署最
广泛的入口控制器，已正式宣布进入仅维护模式：项目维护者承诺尽力维护到 2026 年 3
月，之后将不再发布新版本、不修复 bug、不修复安全漏洞。近几年已有多个高危 CVE
被披露，安全压力长期存在。

继续依赖一个无人维护的组件，本质上是在给未来的安全与合规埋隐患。2026 年因此成
为一个自然的换挡窗口——不是因为情况已经失控，而是因为迁移窗口明确，主动规划好过
被动应急。

与此同时，**Gateway API** 已经达到 GA（正式可用），成为 Kubernetes 官方推荐的、
基于标准的流量路由配置方式，以更丰富的语义、更清晰的职责分层（基础设施层 vs.
应用层）和持续完善的 conformance 测试集，逐步取代 Ingress API。

参考：
https://kubernetes.io/docs/concepts/services-networking/gateway/

参考：
https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/

## Gateway API 标准

Gateway API 将路由配置划分为三层，对应组织内不同角色的职责：

- **GatewayClass** — 由基础设施提供方或集群管理员所有，声明哪个控制器负责处理
  该 class。
- **Gateway** — 由集群运维人员所有，将监听器绑定到某个 GatewayClass。
- **HTTPRoute / GRPCRoute / TCPRoute / …** — 由应用开发者所有，将路由规则挂载
  到 Gateway。

这种分层解决了 Ingress API 中"一个需求一个注解"的失控蔓延问题，也为大型组织提供
了清晰的权限委托模型。

Gateway API 项目维护一个公开的 conformance 状态页，将实现划分为
**Conformant（完全合规）**、**Partially Conformant（部分合规）** 和
**Stale（过期）**三档。这是目前评估实现成熟度最客观、最可公开验证的参照系。

参考：
https://gateway-api.sigs.k8s.io/implementations/

## Gateway API 推理扩展（GAIE）

在标准 HTTP/TCP 路由之外，Kubernetes 社区还引入了 **Gateway API Inference
Extension（GAIE）**——一套专为 LLM 推理工作负载设计的 CRD 和控制器模式，让网关层
能够感知推理请求的特性。

GAIE 在 Gateway API 基础上新增的核心能力：

- **模型感知负载均衡**：将请求路由到已缓存目标模型或 LoRA adapter 的 KV-cache
  后端，减少缓存未命中的代价。
- **请求优先级感知**：在网关层区分交互式（低延迟优先）流量与批处理（吞吐优先）
  流量。
- **InferencePool 和 InferenceModel CRD**：以结构化方式描述推理后端池及其上
  承载的模型/LoRA adapter。

**重要提示**：GAIE 目前处于 **alpha / Experimental** 阶段，CRD schema 和控制器
接口尚未稳定。官方文档中明确列出的、具备 GAIE 集成的网关实现目前较少，主要有
**Istio**、**kgateway** 和 **NGINX Gateway Fabric**；Envoy Gateway 被标注为
可通过其 `ext-proc` 扩展机制与 GAIE 配合使用的可扩展底座。

将 GAIE 作为一个面向未来的选型维度来考量是合理的——值得评估某个实现是否具备
演进到 GAIE 支持的可信路径，而不是强求当前就有生产级 GAIE 能力。

参考：
https://github.com/kubernetes-sigs/gateway-api-inference-extension/

## 实现方案逐一评测

### Envoy Gateway

**仓库：** https://github.com/envoyproxy/gateway

**Gateway API Conformance：** Conformant（GA）

**概述：** Envoy Gateway 由 Envoy Proxy 社区构建，定位为 Gateway API 的参考实现。
它刻意紧跟标准，因此在评估其他实现与规范的契合程度时，Envoy Gateway 是很好的对
照基线。发布节奏健康，2025–2026 年间持续有版本产出。

**从 ingress-nginx 迁移难度：** 中等。Envoy Gateway 不提供 ingress-nginx 注解
兼容层，迁移需要将规则改写为 Gateway API 资源。`ingress2gateway` 工具可以完成
初步转换，但仍需人工校验和测试。

**GAIE 相关性：** Envoy Proxy 的 `ext-proc`（外部处理）扩展是 GAIE 依赖的架构
模式之一。Envoy Gateway 本身目前尚未被列为 GAIE 的一级实现，但它是一个具备
扩展能力的底座。

**平台前提：** 无特殊要求，不需要替换 CNI 或引入服务网格控制面。

**商业层面：** 纯 Apache 2.0 开源项目，多家厂商提供企业级支持。

**总结：** 适合希望在标准对齐、厂商中立的基础上长期构建的团队。选择 Envoy
Gateway 意味着接受"干净迁移而非快速注解兼容"的路径成本。

### NGINX Gateway Fabric

**仓库：** https://github.com/nginx/nginx-gateway-fabric

**Gateway API Conformance：** Conformant（GA）

**概述：** NGINX Gateway Fabric 是 NGINX 项目官方的 Gateway API 实现，提供了在
NGINX 体系内"从 Ingress 平滑升级到 Gateway API"的自然路径——熟悉的 NGINX 数据面，
配以 Gateway API 控制面。

**从 ingress-nginx 迁移难度：** 中等。需要将规则改写为 Gateway API 资源，但底层
NGINX 能力相同，调优和排障时熟悉感较高。NGINX 项目对迁移路径有明确文档。

**GAIE 相关性：** NGINX Gateway Fabric 出现在 GAIE 实现列表中，NGINX 文档包含
GAIE 集成示例，并正确标注了 alpha 阶段风险。

**平台前提：** 无特殊要求。

**商业层面：** NGINX Gateway Fabric 本身开源，使用 NGINX Open Source（免费）。
NGINX Plus 特性（高级负载均衡、主动健康检查、JWT 认证等）需要 F5/NGINX 的付费
订阅授权。如有 Plus 特性需求，需将此纳入总拥有成本评估。

**总结：** 对于已有 NGINX 基础设施且希望向 Gateway API 演进而不更换数据面的团队
是实用选择。开源版与 Plus 订阅版的功能边界需要提前摸清。

### Traefik

**仓库：** https://github.com/traefik/traefik

**Gateway API Conformance：** Conformant（GA）

**概述：** Traefik 是一款成熟、社区庞大的反向代理与负载均衡器。它同时原生支持
Ingress API 和 Gateway API，是少数几个在迁移过渡期内可以并行运行两套 API 的实现
之一，弹性较高。

**从 ingress-nginx 迁移难度：** 低到中等。Traefik 官方文档专门提供了从
ingress-nginx 迁移的指引，包含注解兼容性提示，是目前迁移路径最具可操作性的选项
之一。

参考：
https://doc.traefik.io/traefik/migration/v2-to-v3/

**GAIE 相关性：** Traefik 目前不在 GAIE 网关实现列表中。更适合定位为强大的通用
Kubernetes 入口与路由方案，而非 AI 推理网关的主选项。

**平台前提：** 无特殊要求。

**商业层面：** Traefik Proxy 为开源（MIT License）。Traefik Enterprise（高级 API
管理、商业支持）和 Traefik Hub（连接即服务）是 Traefik Labs 的付费产品。对于绝
大多数 Kubernetes 入口场景，开源版完全够用，无需付费授权。

**总结：** 综合能力突出，尤其适合需要快速迁移或看重生态广度的团队。注解兼容性
指引切实降低了迁移风险。

### kgateway（前身 Gloo）

**仓库：** https://github.com/kgateway-dev/kgateway

**Gateway API Conformance：** Conformant（GA）

**概述：** kgateway 是 CNCF Sandbox 项目，由最初由 Solo.io 开发的 Gloo 项目演进
而来。进入 CNCF Sandbox 带来了更中立的治理结构和更广泛的社区参与。项目实现了
Gateway API 并具备丰富的扩展模型。

**从 ingress-nginx 迁移难度：** 中等。项目支持通过 `ingress2gateway` 工具链完成
Ingress 到 Gateway API 的初步转换，文档涵盖了从注解驱动配置迁移到 Gateway API
标准扩展的路径。

**GAIE 相关性：** kgateway 是 GAIE 最明确支持的网关实现之一，在 GAIE 网关实现
列表中有突出展示。对于希望将 AI 推理路由纳入近期规划的团队，这是一个加分项。

**平台前提：** 无特殊要求。

**商业层面：** 开源版 kgateway 是 CNCF 治理的版本。Solo.io 提供商业发行版
Gloo Platform，包含额外企业特性和支持。建议先评估开源版是否满足需求，再决定是
否需要商业授权。

**治理说明：** 从单一厂商项目（Solo.io/Gloo）向 CNCF 治理项目的过渡是正面信号，
但这一过渡仍处于相对早期阶段。建议在评估时关注社区健康指标（贡献者多样性、发布
节奏、治理成熟度）。

**总结：** 技术能力扎实、标准对齐良好，GAIE 支持是明显亮点。如果 AI 推理路由
是近期需求，值得认真评估。

### Cilium

**仓库：** https://github.com/cilium/cilium（Ingress/Gateway 文档：
https://docs.cilium.io/en/stable/network/servicemesh/ingress/）

**Gateway API Conformance：** Conformant（GA）

**概述：** Cilium 将 Gateway API 作为其基于 eBPF 的网络、安全和可观测性平台的
组成部分来实现。高性能数据面（eBPF）、网络策略与 Gateway API 在单一栈内的组合，
对于希望减少组件数量的团队在架构上很有吸引力。

**从 ingress-nginx 迁移难度：** 高。迁移到 Cilium 的 Gateway 实现不仅是路由层
的变更——通常意味着将 Cilium 作为集群 CNI 引入。对于已运行其他 CNI（Flannel、
Calico 等）的集群，这是一次重量级的平台操作。

**GAIE 相关性：** Cilium 更适合定位为高性能标准网关与服务网格平台，而非 GAIE
的主角。其 ext-proc 扩展能力理论上可以与 GAIE 模式结合，但目前不在 GAIE 实现
列表中。

**平台前提：** Cilium 的完整特性集对 Linux 内核版本有要求，大多数核心功能需要
内核 5.10+，部分能力需要 5.15+。**国内存量服务器环境中，存在较多较低版本内核的
情况，在做决策前务必对全集群内核版本进行审计。** 这是 Cilium 落地的真实门槛，
不可忽视。

**商业层面：** Apache 2.0 开源（CNCF Graduated）。Isovalent（已被 Cisco 收购）
提供商业发行版与企业支持。

**总结：** 对于新建集群或已运行 Cilium 的集群是极具吸引力的选项。内核版本要求
是真实的采用壁垒，内核升级路径受限的环境请勿贸然规划此迁移。

### Istio

**仓库：** https://github.com/istio/istio

**Gateway API Conformance：** Conformant（GA）

**概述：** Istio 是 CNCF Graduated 的服务网格，同时实现了 Gateway API 用于入口
流量管理。它是生态中成熟度最高、部署最广泛的实现之一。`minimal` 安装配置可以降
低只需要入口路由、不需要完整网格能力的团队的运维开销。

**从 ingress-nginx 迁移难度：** 高。即使采用最小安装，Istio 也会引入控制面
（istiod）、额外 CRD 和全新运维模式。路由规则从注解到 Gateway API 资源的改写
工作量与其他实现相当，但平台层面的引入成本更高。

**GAIE 相关性：** Istio 是 GAIE 主要支持的网关实现之一，在 GAIE 项目文档中有
明确列出。对于已经在运行 Istio 或计划投资同时覆盖 AI 推理路由的网格平台的团队，
这是重要加分项。

**平台前提：** 内核版本无特殊要求，但 Istio 控制面（相比独立入口控制器）会引入
可观的资源开销（CPU、内存）和操作复杂度。

**商业层面：** 开源（Apache 2.0，CNCF Graduated）。多家厂商（Solo.io、Tetrate
等）提供商业发行版和支持。

**总结：** 适合已经在 Istio 生态中的组织或正在规划完整服务网格部署的团队。运维
复杂度是客观存在的——请评估是否真的需要网格能力，而不只是入口路由。

### Contour

**仓库：** https://github.com/projectcontour/contour

**Gateway API Conformance：** Partially Conformant（GA）

**概述：** Contour 是基于 Envoy Proxy 的 CNCF Incubating 项目，同时支持 Ingress
API、其自有的 `HTTPProxy` CRD（提供了委托路由、加权路由等 Ingress API 不支持的
能力）以及 Gateway API。**Partially Conformant** 状态意味着部分 conformance 测试
尚未通过，选型时需仔细核查你所关心的具体能力是否已覆盖。

**从 ingress-nginx 迁移难度：** 中等。HTTPProxy CRD 提供了一个过渡台阶——团队可
以先从 Ingress 注解迁移到 HTTPProxy，随着 Gateway API 支持成熟再进一步迁移。

**GAIE 相关性：** 目前不在 GAIE 实现列表中。

**平台前提：** 无特殊要求。

**商业层面：** Apache 2.0 开源，无需商业授权。

**总结：** 标准入口场景的稳健选项。Partially Conformant 的 Gateway API 状态需要
结合你的具体功能需求仔细对照。

### Higress

**仓库：** https://github.com/alibaba/higress

**Gateway API Conformance：** 截至撰写本文时，未出现在 Gateway API 官方实现页
中。这不代表它不支持 Gateway API 特性，但意味着该实现尚未向 Gateway API 项目
提交 conformance 测试结果，标准化状态存在不确定性。

**概述：** Higress 是阿里巴巴开源的网关，活跃维护，核心卖点之一是对 Ingress
注解的兼容性——尤其面向从 ingress-nginx 迁移的场景。它具备基于 WASM 的插件扩展
能力，以及一批面向 AI 网关场景（模型路由、限速、Token 计量）的功能，在 GAIE
概念上有所呼应，尽管实现路径不同。

**从 ingress-nginx 迁移难度：** 低。Higress 明确对标 ingress-nginx 注解兼容，
是注解量较大的团队迁移阻力最小的选项之一。

**GAIE 相关性：** Higress 具备面向 Alibaba Cloud 生态开发的 AI 网关特性，与 GAIE
目标在方向上相近，但实现早于 GAIE 标准，尚未与 GAIE CRD 正式对齐。建议以"相关
但独立"的 AI 网关能力来理解，而非 GAIE 合规实现。

**平台前提：** 无特殊要求。

**商业层面：** 开源（Apache 2.0）。阿里云提供托管版本。项目在国内云原生社区
活跃度较高。

**总结：** 对于有大量 ingress-nginx 注解积累的团队，或主要在阿里云生态下运行的
团队，值得优先评估。如果 Gateway API 标准合规是硬性要求，注意跟进其正式
conformance 进展。对于性能提升方面的声称，建议关注信息来源属性（项目方陈述或
独立第三方基准测试），保持合理预期。

### HAProxy Ingress

**仓库：** https://github.com/jcmoraisjr/haproxy-ingress

**Gateway API Conformance：** 未出现在 Gateway API 官方实现页中。

**概述：** HAProxy Ingress 提供以 HAProxy 为后端的 Kubernetes Ingress 控制器，
背后是经过数十年生产验证的高性能负载均衡器。对于有 HAProxy 既有技术积累的团队
是合理选项。

**从 ingress-nginx 迁移难度：** 中等。Ingress API 支持完善，但 Gateway API
支持尚未达到 conformance 级别。规划 Gateway API 迁移的团队未来可能还需要做
一次工具切换。

**GAIE 相关性：** 不在 GAIE 实现列表中。

**总结：** 对于需要 HAProxy 特定性能特性或功能集的团队是实用选项。对于将
Gateway API 原生能力或 GAIE 列为优先项的团队，不是首选。

### Kong Ingress Controller

**仓库：** https://github.com/Kong/kubernetes-ingress-controller

**Gateway API Conformance：** Partially Conformant（GA）

**概述：** Kong Ingress Controller 将 Kong API 网关能力（限速、认证、插件生态）
带入 Kubernetes。同时支持 Ingress 和 Gateway API。Partially Conformant 状态意味
着部分 Gateway API conformance 测试尚未通过。

**从 ingress-nginx 迁移难度：** 中等。Ingress 和 Gateway API 均支持，Kong 自身
也有针对高级特性的 CRD。`ingress2gateway` 工具可以辅助初步转换。

**GAIE 相关性：** 目前不在 GAIE 实现列表中。

**商业层面：** 开源版 Kong Ingress Controller 免费可用。Kong Inc. 提供 Kong
Konnect、Kong Gateway Enterprise 及托管云服务，含开发者门户、分析、RBAC、
支持 SLA 等高级特性。社区版与企业版之间的功能差距对于有 API 管理需求的组织
是实质性的，**建议在决策前明确列出所需功能对应的版本和价格**。

**总结：** 对于开箱即用地需要 API 管理特性（限速、Key Auth、OAuth、插件生态）
的团队是强力选项。企业版授权费用应纳入总拥有成本分析，避免选型后的预算意外。

## 场景化选型指南

**场景一：快速从 ingress-nginx 迁移，最小化改写工作量**
→ **Traefik** 或 **Higress**。两者均提供明确的 ingress-nginx 迁移指引。
若 Gateway API conformance 是优先项，选 Traefik；若注解兼容深度是优先项，
选 Higress。

**场景二：以标准为先，面向 Gateway API 长期建设**
→ **Envoy Gateway** 或 **NGINX Gateway Fabric**。两者均为 Conformant（GA），
Envoy Gateway 更偏厂商中立；NGINX Gateway Fabric 更适合已有 NGINX 积累的团队。

**场景三：AI 推理路由（GAIE）是近期需求**
→ **Istio**、**kgateway** 或 **NGINX Gateway Fabric**。三者是目前活跃推进
GAIE 集成的实现。请记住 GAIE 仍处于 alpha 阶段。

**场景四：平台整合（入口 + 网络策略 + 网格）**
→ **Cilium**（内核版本满足前提）或 **Istio**（需要完整网格能力）。两者迁移
成本均较高，需充分评估。

**场景五：需要 API 管理特性（限速、插件、认证）**
→ **Kong Ingress Controller** 或 **Traefik Enterprise**。务必仔细评估开源版
与付费版之间的功能边界。

## 汇总对比表

| 实现 | Gateway API Conformance | Ingress 迁移难度 | GAIE 支持 | 平台/内核要求 | 商业层面关键点 |
| --- | --- | --- | --- | --- | --- |
| Envoy Gateway | Conformant (GA) | 中等 | 可扩展底座 | 无特殊 | 纯开源 |
| NGINX Gateway Fabric | Conformant (GA) | 中等 | 已列入（alpha） | 无特殊 | Plus 特性需授权 |
| Traefik | Conformant (GA) | 低到中等 | 未列入 | 无特殊 | Enterprise/Hub 付费 |
| kgateway | Conformant (GA) | 中等 | 已列入（alpha） | 无特殊 | 商业发行版可选 |
| Cilium | Conformant (GA) | 高 | 未列入 | 内核 5.10+ | 商业发行版可选 |
| Istio | Conformant (GA) | 高 | 已列入（alpha） | 无特殊（控制面重） | 商业发行版可选 |
| Contour | Partially Conformant (GA) | 中等 | 未列入 | 无特殊 | 纯开源 |
| Higress | 未在 conformance 列表 | 低 | 概念相近 | 无特殊 | 阿里云托管版可选 |
| HAProxy Ingress | 未在 conformance 列表 | 中等 | 未列入 | 无特殊 | 纯开源 |
| Kong KIC | Partially Conformant (GA) | 中等 | 未列入 | 无特殊 | 企业版功能差距显著 |

## 参考资料

- Gateway API 官网：https://gateway-api.sigs.k8s.io/
- Gateway API 实现列表：https://gateway-api.sigs.k8s.io/implementations/
- Gateway API Inference Extension：https://github.com/kubernetes-sigs/gateway-api-inference-extension/
- Kubernetes Ingress 控制器：https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/
- Kubernetes Gateway 概念：https://kubernetes.io/docs/concepts/services-networking/gateway/
- ingress2gateway 迁移工具：https://github.com/kubernetes-sigs/ingress2gateway
- Envoy Gateway：https://github.com/envoyproxy/gateway
- NGINX Gateway Fabric：https://github.com/nginx/nginx-gateway-fabric
- Traefik：https://github.com/traefik/traefik
- kgateway：https://github.com/kgateway-dev/kgateway
- Cilium：https://docs.cilium.io/en/stable/network/servicemesh/ingress/
- Istio：https://istio.io/
- Contour：https://github.com/projectcontour/contour
- Higress：https://github.com/alibaba/higress
- HAProxy Ingress：https://github.com/jcmoraisjr/haproxy-ingress
- Kong KIC：https://github.com/Kong/kubernetes-ingress-controller
