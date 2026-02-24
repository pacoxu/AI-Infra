---
status: Active
maintainer: pacoxu
last_updated: 2026-02-24
tags: kubernetes, ingress, gateway-api, networking, ai-gateway, gaie
---

# Ingress to Gateway API: Evaluating Kubernetes Ingress Controller Implementations

**Note:** Some content was generated with AI assistance. Please verify details
before using in production environments. All conformance and activity data
was collected around 2026-02-24.

## Table of Contents

- [Background: Why This Matters Now](#background-why-this-matters-now)
- [The Gateway API Standard](#the-gateway-api-standard)
- [Gateway API Inference Extension (GAIE)](#gateway-api-inference-extension-gaie)
- [Implementation Comparison](#implementation-comparison)
  - [Envoy Gateway](#envoy-gateway)
  - [NGINX Gateway Fabric](#nginx-gateway-fabric)
  - [Traefik](#traefik)
  - [kgateway (formerly Gloo)](#kgateway-formerly-gloo)
  - [Cilium](#cilium)
  - [Istio](#istio)
  - [Contour](#contour)
  - [Higress](#higress)
  - [HAProxy Ingress](#haproxy-ingress)
  - [Kong Ingress Controller](#kong-ingress-controller)
- [Selection Guide by Scenario](#selection-guide-by-scenario)
- [Summary Table](#summary-table)
- [References](#references)

## Background: Why This Matters Now

The Kubernetes ingress ecosystem is at an inflection point. **Ingress NGINX**,
the most widely deployed ingress controller, has entered a maintenance-only
phase, with the project maintainers committing only to best-effort support
through March 2026. After that, no new releases, bug fixes, or security patches
are planned. Several high-severity CVEs in recent years have already raised
security concerns for many production deployments.

This situation makes 2026 a natural forcing function: if you are still running
ingress-nginx in production, you need a migration plan — not because the sky is
falling, but because continuing to rely on an unmaintained component is a risk
that compounds over time.

At the same time, the **Gateway API** has reached general availability and is
now the official, standards-based way to configure Kubernetes traffic routing.
It supersedes the `Ingress` API with richer semantics, better role-based
separation (infrastructure vs. application concerns), and a growing conformance
test suite.

Reference:
https://kubernetes.io/docs/concepts/services-networking/gateway/

Reference:
https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/

## The Gateway API Standard

Gateway API organizes routing configuration into three layers, intentionally
mapped to different organizational roles:

- **GatewayClass** — owned by the infrastructure provider (or cluster admin),
  declares which controller handles the class.
- **Gateway** — owned by the cluster operator, binds a listener to a
  GatewayClass.
- **HTTPRoute / GRPCRoute / TCPRoute / …** — owned by the application developer,
  attaches routing rules to a Gateway.

This separation reduces the "one annotation per workaround" sprawl that
plagued the Ingress API, and gives large organizations a clean delegation model.

The Gateway API project maintains a public conformance status page that grades
implementations as **Conformant**, **Partially Conformant**, or **Stale**.
This is the most objective, publicly verifiable proxy for standards maturity
available at the time of writing.

Reference:
https://gateway-api.sigs.k8s.io/implementations/

## Gateway API Inference Extension (GAIE)

Beyond standard HTTP/TCP routing, the Kubernetes community has introduced
**Gateway API Inference Extension (GAIE)** — a set of CRDs and controller
patterns designed to make gateway-level routing aware of LLM inference
workloads.

Key capabilities GAIE adds on top of Gateway API:

- **Model-aware load balancing**: routing requests to the backend that holds
  the target model or adapter in KV-cache, reducing cache miss penalties.
- **Per-request criticality**: distinguishing interactive (low-latency) from
  batch (throughput-oriented) traffic at the gateway layer.
- **InferencePool and InferenceModel CRDs**: structured way to describe a pool
  of inference backends and the model/LoRA adapter hosted on them.

**Important caveat**: GAIE is currently **alpha / Experimental**. The CRD
schemas and controller interfaces are not yet stable. The official documentation
lists only a small set of gateway implementations as having active GAIE
integration: **Istio**, **kgateway**, and **NGINX Gateway Fabric** are the
most explicitly called out. Envoy Gateway is noted as an extensible base that
could be used with GAIE's `ext-proc` mechanism. Other implementations may
develop GAIE support over time but are not in the official list today.

Treat GAIE as a forward-looking selection criterion — it is worth asking
whether a given implementation has a credible path to GAIE support, rather
than requiring production-ready GAIE today.

Reference:
https://github.com/kubernetes-sigs/gateway-api-inference-extension/

## Implementation Comparison

### Envoy Gateway

**Repository:** https://github.com/envoyproxy/gateway

**Gateway API Conformance:** Conformant (GA)

**Summary:** Envoy Gateway is built by the Envoy Proxy community as a
reference-quality implementation of Gateway API. It deliberately stays close
to the standard, making it useful as a benchmark when evaluating how well other
implementations track the spec. The release cadence is healthy, with versions
published regularly in 2025–2026.

**Migration from ingress-nginx:** Medium cost. Envoy Gateway does not provide
ingress-nginx annotation compatibility; migration requires rewriting rules in
Gateway API resources. The `ingress2gateway` tool can automate a first pass,
but manual review and testing are still needed.

**GAIE:** Envoy Proxy's `ext-proc` (external processing) extension is one of
the architectural patterns GAIE relies on. Envoy Gateway itself is not listed
as a first-class GAIE implementation yet, but it is an extensible foundation.

**Platform requirements:** Standard. Does not require replacing the CNI or
adding a service mesh control plane.

**Commercial considerations:** Envoy Gateway is a pure Apache 2.0 open-source
project. Enterprise support is available from multiple vendors.

**Assessment:** A strong choice for teams that want to build on a standards-
aligned, vendor-neutral foundation and are willing to invest in a clean
migration rather than a quick annotation-swap.

### NGINX Gateway Fabric

**Repository:** https://github.com/nginx/nginx-gateway-fabric

**Gateway API Conformance:** Conformant (GA)

**Summary:** NGINX Gateway Fabric is the official Gateway API implementation
from the NGINX project. It provides a natural upgrade path within the NGINX
family — the familiar NGINX data plane, but with a Gateway API control surface
instead of Ingress annotations.

**Migration from ingress-nginx:** Medium cost. Gateway API resources need to
be rewritten, but the underlying NGINX capabilities are familiar, which reduces
surprises during tuning and troubleshooting. The NGINX project documents this
migration path explicitly.

**GAIE:** NGINX Gateway Fabric appears in the GAIE implementation list and
NGINX documentation includes examples for the GAIE integration. The
documentation correctly notes that GAIE features carry alpha-level risk.

**Platform requirements:** Standard.

**Commercial considerations:** NGINX Gateway Fabric is open source and uses
NGINX Open Source. NGINX Plus features (advanced load balancing, active health
checks, JWT authentication, etc.) require a subscription license from F5/NGINX.
Factor this into total cost of ownership if Plus features are needed.

**Assessment:** A pragmatic choice for organizations already operating NGINX-
based infrastructure who want to move to Gateway API without changing the data
plane. Be clear-eyed about what is available in the open-source tier versus
the Plus subscription.

### Traefik

**Repository:** https://github.com/traefik/traefik

**Gateway API Conformance:** Conformant (GA)

**Summary:** Traefik is a well-established, widely deployed reverse proxy and
load balancer with a large open-source community. It supports both the Ingress
API and Gateway API natively, making it one of the more flexible options for
teams that need to operate both APIs in parallel during a migration window.

**Migration from ingress-nginx:** Low to medium cost. Traefik's official
documentation includes guidance specifically for migrating from ingress-nginx,
including annotation compatibility hints. This makes it one of the most
practical options for teams looking for a fast migration path.

Reference:
https://doc.traefik.io/traefik/migration/v2-to-v3/

**GAIE:** Traefik is not currently listed among the GAIE gateway implementations.
Position it as a strong general-purpose Kubernetes ingress and routing solution
rather than a primary AI inference gateway.

**Platform requirements:** Standard.

**Commercial considerations:** Traefik Proxy is open source (MIT license).
Traefik Enterprise (advanced API management, commercial support) and Traefik
Hub (connectivity-as-a-service) are paid products from Traefik Labs. The open-
source proxy is fully functional for the vast majority of Kubernetes ingress
use cases without any paid license.

**Assessment:** Excellent all-around choice, particularly for teams that need
to migrate quickly or that value broad ecosystem integration. The annotation
compatibility guidance lowers the practical migration risk.

### kgateway (formerly Gloo)

**Repository:** https://github.com/kgateway-dev/kgateway

**Gateway API Conformance:** Conformant (GA)

**Summary:** kgateway is a CNCF Sandbox project that evolved from the Gloo
project, which was originally developed and maintained by Solo.io. The move to
CNCF Sandbox provides more neutral governance and a broader community stewardship
model. The project implements Gateway API with a rich extension model.

**Migration from ingress-nginx:** Medium cost. The project supports a
translation path from Ingress resources to Gateway API via the `ingress2gateway`
toolchain, and its documentation covers the migration approach for moving from
annotation-heavy configurations to standard Gateway API extensions.

**GAIE:** kgateway is one of the most explicitly supported GAIE implementations.
It appears prominently in the GAIE gateway list, making it a strong choice for
teams that want to invest in AI inference routing capabilities alongside standard
ingress.

**Platform requirements:** Standard.

**Commercial considerations:** The open-source kgateway is the CNCF-governed
version. Solo.io offers a commercial distribution called Gloo Platform with
additional enterprise features and support. Organizations should evaluate
whether the open-source tier meets their needs before committing to commercial
licensing.

**Governance note:** The transition from a single-vendor project (Solo.io/Gloo)
to a CNCF-governed project is a positive signal, but the project is still
relatively early in that transition. Prospective users should monitor community
health metrics (contributor diversity, release cadence, governance maturity)
as part of their evaluation.

**Assessment:** A capable, standards-aligned implementation with strong GAIE
credentials. Worth evaluating seriously if AI inference routing is a near-term
requirement.

### Cilium

**Repository:** https://github.com/cilium/cilium (Ingress/Gateway docs at
https://docs.cilium.io/en/stable/network/servicemesh/ingress/)

**Gateway API Conformance:** Conformant (GA)

**Summary:** Cilium implements Gateway API as part of its broader eBPF-based
networking, security, and observability platform. The combination of high-
performance data-plane (eBPF), network policy, and Gateway API in a single
stack is architecturally attractive for organizations that want to minimize
the number of components.

**Migration from ingress-nginx:** High cost. Migrating to Cilium's Gateway
implementation is not just a routing-layer change — it typically means adopting
Cilium as the cluster CNI. For clusters already running other CNIs (Flannel,
Calico, etc.), this is a significant operational undertaking.

**GAIE:** Cilium is best positioned as a high-performance standard gateway and
service mesh platform rather than a primary GAIE implementation. Its ext-proc
extension capability could theoretically be used with GAIE patterns, but it is
not in the current GAIE implementation list.

**Platform requirements:** Cilium's full feature set requires a reasonably
modern Linux kernel. Many features require kernel 5.10+, with some capabilities
needing 5.15+. Organizations with large fleets of servers running older kernels
(common in some enterprise and on-premises environments) should audit their
kernel versions before committing to Cilium.

**Commercial considerations:** Cilium is Apache 2.0 open source (CNCF Graduated).
Isovalent (acquired by Cisco) offers a commercial distribution with enterprise
support.

**Assessment:** A compelling choice for greenfield clusters or clusters
already running Cilium. The kernel requirement is a genuine adoption barrier
for organizations with constrained kernel upgrade paths. Do not plan this
migration without first auditing kernel versions across your fleet.

### Istio

**Repository:** https://github.com/istio/istio

**Gateway API Conformance:** Conformant (GA)

**Summary:** Istio is a CNCF Graduated service mesh that also implements
Gateway API for ingress traffic. It is one of the most mature and widely
deployed implementations in the ecosystem. The `minimal` install profile can
reduce operational overhead for teams that only need ingress routing without
the full mesh.

**Migration from ingress-nginx:** High cost. Even with a minimal install,
adopting Istio introduces a control plane (istiod), additional CRDs, and a
new operational model. The migration from ingress annotations to Gateway API
resources is comparable to other implementations, but the platform overhead
is higher.

**GAIE:** Istio is one of the primary GAIE-supported gateway implementations.
The GAIE project explicitly lists Istio integration, making it a strong
candidate for teams that are already running Istio or planning to invest in
a mesh platform that also handles AI inference routing.

**Platform requirements:** Standard in terms of kernel version. However,
Istio's control plane adds non-trivial resource overhead (CPU, memory) and
operational complexity compared to a standalone ingress controller.

**Commercial considerations:** Istio is open source (Apache 2.0, CNCF
Graduated). Commercial distributions and support are available from multiple
vendors (Solo.io, Tetrate, etc.).

**Assessment:** A mature, trusted platform for organizations already invested
in Istio or planning a full service mesh deployment. The operational complexity
is real — evaluate whether you need the mesh capabilities, not just the
ingress routing.

### Contour

**Repository:** https://github.com/projectcontour/contour

**Gateway API Conformance:** Partially Conformant (GA)

**Summary:** Contour is a CNCF Incubating project built on Envoy Proxy. It
supports the Ingress API, its own `HTTPProxy` CRD (which adds features not
available in the Ingress API, such as delegation and weighted routing), and
Gateway API. The `Partially Conformant` status on the Gateway API conformance
page means some conformance tests are not yet passing; users should review
which specific capabilities are and are not supported.

**Migration from ingress-nginx:** Medium cost. Contour's HTTPProxy CRD
provides a migration stepping stone — teams can move from Ingress annotations
to HTTPProxy progressively, then to Gateway API as support matures.

**GAIE:** Contour is not currently in the GAIE implementation list.

**Platform requirements:** Standard.

**Commercial considerations:** Apache 2.0 open source. No commercial licensing
required for the project itself.

**Assessment:** A stable, well-governed option for standard ingress use cases.
The Partially Conformant Gateway API status should be evaluated carefully
against your specific feature requirements.

### Higress

**Repository:** https://github.com/alibaba/higress

**Gateway API Conformance:** Not listed on the Gateway API official
implementations page at the time of writing. This does not mean it does not
implement Gateway API features, but it does mean the implementation has not
submitted conformance test results to the Gateway API project.

**Summary:** Higress is an open-source gateway developed by Alibaba that is
actively maintained with a strong focus on Ingress annotation compatibility —
particularly for teams migrating away from ingress-nginx. It has WASM-based
plugin extensibility and a number of AI gateway features that make it relevant
to the GAIE conversation, even if it is not formally in the GAIE list.

**Migration from ingress-nginx:** Low cost. Higress explicitly targets
ingress-nginx annotation compatibility, making it one of the lowest-friction
migration paths for teams with large annotation-heavy configurations.

**GAIE:** Higress has AI gateway features (model routing, rate limiting,
token counting) developed for the Alibaba Cloud ecosystem. These align
conceptually with GAIE goals, but the implementation predates the GAIE
standard and is not yet formally aligned with GAIE CRDs. Treat this as a
"related but distinct" AI gateway capability rather than GAIE compliance.

**Platform requirements:** Standard.

**Commercial considerations:** Open source (Apache 2.0). Aliyun/Alibaba Cloud
offers a managed version. Community is active, particularly within the Chinese
cloud-native ecosystem.

**Assessment:** Worth evaluating for teams with significant ingress-nginx
annotation debt, or for teams operating primarily within the Alibaba Cloud
ecosystem. The lack of formal Gateway API conformance test results is worth
tracking if standards compliance matters to your organization.

### HAProxy Ingress

**Repository:** https://github.com/jcmoraisjr/haproxy-ingress

**Gateway API Conformance:** Not listed on the Gateway API official
implementations page.

**Summary:** HAProxy Ingress provides a Kubernetes Ingress controller backed
by HAProxy, a proven high-performance load balancer with decades of production
history. It is a reasonable choice for teams with existing HAProxy expertise.

**Migration from ingress-nginx:** Medium cost. The Ingress API is supported,
but Gateway API support is not yet at conformance level. Teams planning to
migrate to Gateway API will eventually need to make another tool change.

**GAIE:** Not in the GAIE implementation list.

**Assessment:** A solid option for teams that need the specific performance
characteristics or feature set of HAProxy. Not the strongest choice for teams
investing in a Gateway API-native future or GAIE.

### Kong Ingress Controller

**Repository:** https://github.com/Kong/kubernetes-ingress-controller

**Gateway API Conformance:** Partially Conformant (GA)

**Summary:** Kong Ingress Controller brings Kong's API gateway capabilities
(rate limiting, authentication, plugins) to Kubernetes. It supports both
Ingress and Gateway API. The `Partially Conformant` status means some Gateway
API conformance tests are not yet passing.

**Migration from ingress-nginx:** Medium cost. Both Ingress and Gateway API
are supported. Kong provides its own CRDs for advanced features. The
`ingress2gateway` tool can help with a first-pass conversion.

**GAIE:** Kong is not currently in the GAIE implementation list.

**Commercial considerations:** The open-source Kong Ingress Controller is
available at no cost. Kong Inc. offers Kong Konnect, Kong Gateway Enterprise,
and managed cloud services with advanced features (developer portal, analytics,
RBAC, support SLAs). The feature gap between community and enterprise editions
is meaningful for organizations with API management requirements; evaluate costs
explicitly.

**Assessment:** Strong for teams that need API management features (rate
limiting, key auth, OAuth, plugins) out of the box. The enterprise tier
pricing should be factored into total cost of ownership analysis.

## Selection Guide by Scenario

**Scenario 1: Fast migration from ingress-nginx, minimize rewrite effort**
→ **Traefik** or **Higress**. Both provide explicit ingress-nginx migration
guidance. Traefik is the stronger choice if Gateway API conformance is a
priority; Higress if annotation compatibility depth is the priority.

**Scenario 2: Standards-first, build for Gateway API long-term**
→ **Envoy Gateway** or **NGINX Gateway Fabric**. Both are fully Conformant
(GA). Envoy Gateway is the more vendor-neutral choice; NGINX Gateway Fabric
is natural for teams already using NGINX.

**Scenario 3: AI inference routing (GAIE) is a near-term requirement**
→ **Istio**, **kgateway**, or **NGINX Gateway Fabric**. These are the
implementations with active GAIE integration. Remember GAIE is still alpha.

**Scenario 4: Full platform consolidation (ingress + network policy + mesh)**
→ **Cilium** (if kernel requirements are met) or **Istio** (if full mesh
capabilities are needed). Both carry higher migration costs.

**Scenario 5: API management features (rate limiting, plugins, auth)**
→ **Kong Ingress Controller** or **Traefik Enterprise**. Evaluate open-source
vs. paid tier feature gaps carefully.

## Summary Table

| Implementation | Gateway API Conformance | Ingress Migration Cost | GAIE Support | Kernel/Platform Req | Key Commercial Note |
| --- | --- | --- | --- | --- | --- |
| Envoy Gateway | Conformant (GA) | Medium | Extensible base | Standard | Pure open source |
| NGINX Gateway Fabric | Conformant (GA) | Medium | Listed (alpha) | Standard | Plus features need license |
| Traefik | Conformant (GA) | Low–Medium | Not listed | Standard | Enterprise/Hub are paid |
| kgateway | Conformant (GA) | Medium | Listed (alpha) | Standard | Commercial dist. available |
| Cilium | Conformant (GA) | High | Not listed | Kernel 5.10+ | Commercial dist. available |
| Istio | Conformant (GA) | High | Listed (alpha) | Standard (heavier) | Commercial dist. available |
| Contour | Partially Conformant (GA) | Medium | Not listed | Standard | Pure open source |
| Higress | Not in conformance list | Low | Conceptually related | Standard | Alibaba Cloud managed |
| HAProxy Ingress | Not in conformance list | Medium | Not listed | Standard | Pure open source |
| Kong KIC | Partially Conformant (GA) | Medium | Not listed | Standard | Enterprise tier significant |

## References

- Gateway API: https://gateway-api.sigs.k8s.io/
- Gateway API Implementations: https://gateway-api.sigs.k8s.io/implementations/
- Gateway API Inference Extension: https://github.com/kubernetes-sigs/gateway-api-inference-extension/
- Kubernetes Ingress Controllers: https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/
- Kubernetes Gateway concept: https://kubernetes.io/docs/concepts/services-networking/gateway/
- ingress2gateway migration tool: https://github.com/kubernetes-sigs/ingress2gateway
- Envoy Gateway: https://github.com/envoyproxy/gateway
- NGINX Gateway Fabric: https://github.com/nginx/nginx-gateway-fabric
- Traefik: https://github.com/traefik/traefik
- kgateway: https://github.com/kgateway-dev/kgateway
- Cilium: https://docs.cilium.io/en/stable/network/servicemesh/ingress/
- Istio: https://istio.io/
- Contour: https://github.com/projectcontour/contour
- Higress: https://github.com/alibaba/higress
- HAProxy Ingress: https://github.com/jcmoraisjr/haproxy-ingress
- Kong KIC: https://github.com/Kong/kubernetes-ingress-controller
