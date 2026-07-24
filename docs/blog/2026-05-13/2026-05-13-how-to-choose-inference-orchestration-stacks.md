---
status: Active
maintainer: pacoxu
date: 2026-05-13
last_updated: 2026-07-24
tags: inference, orchestration, kubernetes, llm, pd-disaggregation, llm-d, kserve, dynamo, aibrix, kthena, sglang, rbg, vllm
canonical_path: docs/blog/2026-05-13/2026-05-13-how-to-choose-inference-orchestration-stacks.md
source_urls:
  - https://kserve.github.io/website/
  - https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview
  - https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-envoy-ai-gateway
  - https://kserve.github.io/website/blog/cloud-native-ai-inference-kserve-llm-d
  - https://github.com/llm-d/llm-d
  - https://github.com/llm-d/llm-d/releases
  - https://github.com/llm-d/llm-d/releases/tag/v0.8.1
  - https://llm-d.ai/docs/architecture/architecture
  - https://github.com/vllm-project/production-stack
  - https://github.com/vllm-project/production-stack/releases
  - https://docs.vllm.ai/en/latest/deployment/integrations/production-stack.html
  - https://github.com/vllm-project/aibrix
  - https://github.com/vllm-project/aibrix/releases
  - https://github.com/vllm-project/aibrix/releases/tag/v0.7.0
  - https://aibrix.readthedocs.io/latest/getting_started/installation/installation.html
  - https://aibrix.readthedocs.io/latest/designs/aibrix-stormservice.html
  - https://aibrix.readthedocs.io/latest/designs/aibrix-router.html
  - https://aibrix.readthedocs.io/latest/features/autoscaling/metric-based-autoscaling.html
  - https://kthena.volcano.sh/docs/intro
  - https://github.com/volcano-sh/kthena/releases/tag/v1.0.0
  - https://kthena.volcano.sh/docs/v0.2.0/architecture
  - https://github.com/volcano-sh/kthena/blob/main/docs/proposal/modelserving-role-support-leaderworkerset.md
  - https://github.com/volcano-sh/kthena/pull/767
  - https://volcano.sh/en/blog/introducing-kthena-redefining-llm-inference-for-the-cloud-native-era/
  - https://docs.nvidia.com/dynamo/latest/kubernetes-deployment/deployment-guide
  - https://docs.nvidia.com/dynamo/latest/kubernetes-deployment/multinode/grove
  - https://docs.nvidia.com/dynamo/components/planner/planner-guide
  - https://github.com/ai-dynamo/dynamo
  - https://docs.sglang.io/
  - https://docs.sglang.io/advanced_features/router.html
  - https://github.com/sgl-project/sglang/releases
  - https://github.com/sgl-project/rbg
  - https://github.com/kubernetes-sigs/lws/blob/main/keps/766-DisaggregatedSet/README.md
---

# How to choose an inference orchestration stack: AIBrix, Kthena, Dynamo, llm-d, KServe, vLLM Production Stack, and SGLang/RBG

This post is based on public information checked as of **2026-05-13**. It is intended for technical reference only. Real-world outcomes depend heavily on workload shape, GPU and network topology, existing control planes, operating model, and ecosystem fit. A project's current design should not be treated as its final direction. Community openness, activity, and long-term convergence matter at least as much as any single release.

## Summary

A layer-based view helps organize the comparison:

- `vLLM` and `SGLang` are primarily **runtimes / inference engines**
- `vLLM Production Stack` and `llm-d` are primarily **serving stacks**
- `KServe`, `AIBrix`, `Kthena`, and `Dynamo` are primarily **platforms / control planes**
- `RBG` and `LWS/DisaggregatedSet` are primarily **workload primitives / orchestration APIs**

From the current public materials:

- `KServe` has a distinct Generative AI path through `LLMInferenceService`, explicitly built on top of `llm-d`
- `llm-d` is converging toward a fuller distributed serving stack with routing, KV locality, PD, and cluster-level scheduling intelligence
- `vLLM Production Stack` remains closer to an upstream deployment stack than to a unified control plane
- `SGLang` now spans both runtime and gateway concerns; `RBG` covers the multi-role workload API side
- `LWS/DisaggregatedSet` is beginning to turn coordinated multi-LWS updates and revision-aware service orchestration into an upstream primitive
- `AIBrix`, `Kthena`, and `Dynamo` all expose broader platform surfaces, each tied to a different ecosystem and optimization path

## 1. Current landscape

The current generation of inference orchestration stacks is addressing the same broader set of systems problems:

- **role orchestration**: how prefill, decode, router, gateway, and related roles are expressed and coordinated
- **traffic entry**: how routing reacts to topology, cache locality, revision state, and load
- **KV and state locality**: how data locality is maintained across replicas, roles, and nodes
- **scaling**: whether scaling happens per role, per workload, per SLA, or under platform policy
- **rollout and recovery**: how multi-role services coordinate upgrade, rollback, and failure recovery

From the current public materials:

- `KServe` is acting as a unified platform entry point
- `llm-d` is one of the clearest distributed serving paths
- `vLLM Production Stack` is a lighter upstream deployment stack
- `SGLang` now spans runtime and gateway
- `RBG` and `DisaggregatedSet` are closer to upstream workload APIs
- `AIBrix`, `Kthena`, and `Dynamo` are all forming more explicit platform stories

## 2. Layered view

| Layer | Representative projects | Main responsibility |
| --- | --- | --- |
| Runtime / Engine | `vLLM`, `SGLang` | Execute inference inside one pod or a tightly coupled serving backend |
| Serving Stack | `vLLM Production Stack`, `llm-d` | Turn runtimes into routable, observable, scalable cluster services |
| Platform / Control Plane | `KServe`, `AIBrix`, `Kthena`, `Dynamo` | Use CRDs, routers, autoscalers, and policy to manage the inference lifecycle |
| Workload Primitive | `RBG`, `LWS/DisaggregatedSet` | Provide a better Kubernetes API for tightly coordinated multi-role AI workloads |

This separation matters for comparison:

- `KServe / AIBrix / Kthena / Dynamo` are most naturally compared at the platform layer
- `llm-d / vLLM Production Stack / SGLang Gateway` are most naturally compared at the serving-stack layer
- `RBG / LWS / DisaggregatedSet` are most naturally compared at the workload-primitive layer

## 3. KServe

As of `2026-05-13`, KServe positions itself as a **Standardized Distributed Generative and Predictive AI Inference Platform**. Its Generative AI path is expressed through a dedicated `LLMInferenceService`.

The public `0.17` documentation is explicit:

- `LLMInferenceService` is a dedicated CRD for Generative AI workloads
- it is built on top of `llm-d`
- it exposes multi-node inference, PD separation, advanced routing, and DP+EP patterns at the platform API layer
- it retains KServe’s traditional strengths around unified APIs, lifecycle management, Gateway API integration, and governance

In practice, the relationship is:

- `KServe` as the platform entry point and governance layer
- `llm-d` as the distributed serving layer underneath

This combination aligns with environments already centered on standard Kubernetes APIs, unified model delivery, and shared gateway policies.

## 4. llm-d

`llm-d` is currently best understood as a **Kubernetes-native distributed inference serving stack**, not as a general platform and not merely as a `vLLM` deployment template.

As of `v0.8.1` on **2026-06-26**, the public release notes and architecture docs show a fairly complete direction:

- Router and Scheduler as first-class components
- KV cache aware routing
- Prefill/Decode disaggregation
- `LeaderWorkerSet` as one multi-node orchestration path
- variant autoscaling
- integration with the Gateway API inference extension
- a clearer `SGLang` support path

Its emphasis is cluster-level intelligence rather than only runtime-level throughput:

- whether requests preserve prefix-cache locality
- whether prefill and decode land in the right resource pools
- whether routing can make finer endpoint choices than generic load balancing
- whether tail latency and GPU utilization remain stable under large-model and multi-tenant pressure

## 5. vLLM Production Stack

`vLLM Production Stack` is currently closer to an **upstream reference deployment stack**. The official README describes it as **vLLM’s reference system for K8S-native cluster-wide deployment**.

As of `2026-05-07`, the latest release is `vllm-stack-0.1.11`. Its current public shape centers on:

- Helm-based deployment
- a request router
- Prometheus + Grafana observability
- LMCache / KV cache offloading
- a reference path from a single vLLM instance to cluster-wide deployment

The current profile is straightforward:

- closer to upstream `vLLM`
- thinner as a stack
- already includes a usable baseline for routing, observability, and cache offloading

At the same time, it does not aim to act as a unified control plane or offer the governance surface associated with `KServe / AIBrix / Kthena / Dynamo`.

## 6. SGLang, RBG, and LWS/DisaggregatedSet

This group spans runtime, gateway, and workload-primitive concerns.

### 6.1 SGLang

SGLang currently spans both runtime and gateway concerns. Public documentation and releases show a broader surface:

- a high-performance serving framework
- PD disaggregation, HiCache, multiple parallelism modes, and broad hardware support
- `SGLang Model Gateway`, covering HTTP/gRPC/OpenAI-compatible routing, Kubernetes service discovery, PD topologies, observability, and reliability controls
- `Unified Inference Gateway Mode`

The current picture is therefore:

- strong runtime capability
- a growing serving-stack and gateway story

### 6.2 RBG

`RBG` is not primarily about gateway behavior. Its core value lies in `RoleBasedGroup` as a multi-role Kubernetes workload API.

Its README highlights:

- role startup-order dependencies
- automated service discovery
- group-level and role-level elastic scaling
- atomic rollout
- topology-aware placement
- atomic failure recovery
- multiple role backends, including `StatefulSet`, `Deployment`, and `LeaderWorkerSet`

That makes `RBG` mainly valuable as a more natural Kubernetes primitive for distributed multi-role inference services.

### 6.3 LWS / DisaggregatedSet

`DisaggregatedSet` is a new CRD proposed in the `LeaderWorkerSet` project. Its purpose is to collapse what would otherwise be several manually coordinated `LeaderWorkerSet` objects into one resource.

The current KEP-766 draft focuses on a small but important set of problems:

- how multiple LWS instances are upgraded together
- how version consistency across roles is enforced
- how revision-aware Services are created automatically
- how multi-role rollout avoids orphaned workloads and configuration drift

Several design points stand out:

- **`spec.roles`**: each role embeds a full `LeaderWorkerSetTemplateSpec`
- **N-dimensional coordinated rolling update**: roles advance through rollout as one coordinated revision, not as unrelated updates
- **per-revision headless Services**: names like `{name}-{revision}-{role}-prv` provide the basis for revision-aware traffic routing by upper-layer systems such as `llm-d`
- **current scope limits**: no HPA/VPA, no multi-cluster support, and no non-LWS backend support in the current draft

Placed next to `RBG`, the difference is fairly clear:

- `RBG` is more general and can use non-LWS backends
- `DisaggregatedSet` is more explicitly rooted in the LWS ecosystem and focused on coordinated multi-LWS rollout and service orchestration

## 7. AIBrix

`AIBrix` presents a modular platform rather than a single-CRD design.

As of `v0.7.0` on **2026-06-18** and the latest public docs, the main signals are:

- vanilla Kubernetes is a first-class path
- `Envoy Gateway` is a required entry layer
- `KubeRay` is now optional
- `StormService` is one main orchestration path for multi-node inference
- router, KV cache, pod autoscaler, and LoRA/adapter-related capabilities evolve as distinct platform modules

`StormService` matters because it is not merely a PD template. It is structured as:

- `StormService`
- `RoleSet`
- `Pods`

and its public design already includes:

- replica mode
- pooled mode
- top-level rolling / inplace update
- RoleSet-level parallel / sequential / interleaved update
- role-level autoscaling in pooled mode

## 8. Kthena

Kthena explicitly presents itself as a **Kubernetes-native AI serving platform**.

Its main value is not support for one specific workload shape, but rather the way it organizes a set of platform abstractions:

- `ModelBooster`
- `ModelRoute`
- `ModelServer`
- `ModelServing`
- `AutoscalingPolicy`

From the current docs and official blog, several characteristics are stable:

- strong affinity with the `Volcano` scheduling ecosystem
- multi-backend support across `vLLM`, `SGLang`, `Triton`, and `TorchServe`
- request-level intelligent routing
- token-based rate limiting, canary, and failover
- role-aware PD routing
- coordinated role-level P/D autoscaling with optional replica-ratio constraints
- session boost for multi-turn workloads and cache-aware router metrics

Kthena v1.0.0 removed `AutoscalingPolicyBinding`; existing autoscaling targets
must move into `AutoscalingPolicy.spec.homogeneousTarget`,
`heterogeneousTarget`, or `disaggregatedTarget` before upgrading.

At the same time, public proposals and follow-up PRs show ongoing exploration of **LWS API compatibility**. That places LWS more as a compatible northbound interface than as the only internal primitive.

## 9. Dynamo

`Dynamo` is currently best understood as a **performance-system-first inference platform**.

The official documentation presents it as a broader stack:

- `DynamoGraphDeploymentRequest (DGDR)`: the recommended simplified SLA-driven entry point
- `DynamoGraphDeployment (DGD)`: a more direct low-level deployment path
- `Planner`
- `Profiler`
- `Router`
- `KVBM`
- multi-node orchestration through `Grove`

The Kubernetes deployment guide and Grove documentation point in a clear direction:

- the platform layer is carried by `DGDR/DGD + Operator`
- multi-node and multi-role orchestration is mainly delegated to `Grove`
- `Planner` translates SLA intent into deployment shape and scaling behavior

`Grove` itself emphasizes:

- a Kubernetes API for modern AI workloads, especially disaggregated inference
- a unified resource that can express prefill, decode, routing, and related components
- support for multi-level horizontal autoscaling, startup dependencies, and topology-aware scheduling

## 10. Comparison

| Option | Positioning | `role / PD` | Routing / gateway | Scaling | Ecosystem center of gravity |
| --- | --- | --- | --- | --- | --- |
| `KServe` | Unified AI inference platform | Strong, exposed through `LLMInferenceService` | Strong | Strong | Standard Kubernetes platform |
| `llm-d` | Distributed serving stack | Very strong | Very strong | Strong | High-performance distributed LLM serving |
| `vLLM Production Stack` | Upstream reference stack | Present, but not the most distinctive current selling point | Medium to strong | Medium | Pure `vLLM` ecosystem |
| `SGLang` | Runtime + gateway | Very strong | Very strong | Medium to strong | `SGLang` runtime and gateway |
| `RBG` | Multi-role workload API | Core capability | Mostly service discovery | Strong | Generic multi-role primitive |
| `LWS / DisaggregatedSet` | Multi-role primitive on top of LWS | Very strong | Mainly revision-aware Service orchestration | More conservative scaling scope in the current draft | LWS ecosystem |
| `AIBrix` | Modular GenAI infrastructure platform | Very strong, with `StormService / RoleSet` already fairly mature | Strong | Strong, including public role-level autoscaling | Vanilla Kubernetes + platform modules |
| `Kthena` | Volcano-native AI serving platform | Very strong, with `ModelServing / ServingGroup / Role` | Very strong | Very strong | Volcano / scheduling and topology |
| `Dynamo` | Performance-first AI infrastructure platform | Very strong, especially through `DGDR/DGD + Grove` | Very strong | Very strong, with explicit planner emphasis | NVIDIA / multi-node / SLA |

## 11. Scenario view

The cases below are intentionally simplified. The aim is to show ecosystem and infrastructure alignment, not to rank the projects abstractly.

### Volcano environments

`Kthena` sits closest to the `Volcano` scheduling and platform model. Gang scheduling, topology-aware placement, and inference role orchestration can be understood in one ecosystem.

### KServe environments

`KServe + llm-d` is currently the most natural public combination: the former provides the platform entry point and governance layer, while the latter provides the distributed serving layer.

### vLLM environments

`vLLM Production Stack` fits the lighter upstream deployment path. `llm-d` fits the cases where cluster-wide routing, KV locality, and PD orchestration become central concerns.

### NVIDIA-oriented environments

`Dynamo` together with `Grove` places more emphasis on an integrated path across profiler, planner, backend behavior, KV handling, and multi-node orchestration.

### Vanilla Kubernetes environments

`AIBrix` currently presents the clearest platform-modularization path. `Envoy Gateway`, `StormService`, `Router`, `PodAutoscaler`, and `KV Cache` form a relatively complete control-plane story.

### SGLang environments

`SGLang` and `RBG` are more naturally upstream/downstream complements: the former covers runtime and gateway, while the latter covers the multi-role workload API.

### Upstream primitive path

`RBG` and `LWS/DisaggregatedSet` point to two different directions in upstream workload-primitive work:

- `RBG` is more general
- `DisaggregatedSet` is more focused on coordinated multi-role rollout and service orchestration inside the LWS ecosystem

## 12. The boundary of PD disaggregation

PD disaggregation is part of a broader systems design question. Even so, support for PD does not imply that PD is a good fit in every environment.

It tends to make the most sense when:

- prompts are long and outputs are relatively short
- concurrency is high and request shapes vary widely
- prefill and decode prefer meaningfully different hardware or resource pools
- `TTFT` and `TPOT` need to be optimized independently

It deserves more caution when:

- contexts are short or models are small to medium
- concurrency is low
- hardware is homogeneous
- KV transfer and cross-role coordination may erase the gains
- platform observability, routing, and failure handling are not yet mature enough

## Conclusion

As of `2026-05-13`, a practical comparison starts with the layer of the inference system each project is addressing.

From that perspective:

- `vLLM` and `SGLang` are mainly runtimes
- `vLLM Production Stack` and `llm-d` are mainly serving stacks
- `KServe`, `AIBrix`, `Kthena`, and `Dynamo` are mainly platforms
- `RBG` and `LWS/DisaggregatedSet` are mainly workload primitives

Separating the layers makes the roles, boundaries, and composition paths among these projects clearer.
