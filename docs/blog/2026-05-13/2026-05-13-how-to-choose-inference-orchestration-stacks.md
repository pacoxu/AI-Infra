---
status: Active
maintainer: pacoxu
date: 2026-05-13
tags: inference, orchestration, kubernetes, llm, pd-disaggregation, llm-d, kserve, dynamo, aibrix, kthena, sglang, rbg, vllm
canonical_path: docs/blog/2026-05-13/2026-05-13-how-to-choose-inference-orchestration-stacks.md
source_urls:
  - https://kserve.github.io/website/
  - https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview
  - https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-envoy-ai-gateway
  - https://kserve.github.io/website/blog/cloud-native-ai-inference-kserve-llm-d
  - https://github.com/llm-d/llm-d
  - https://github.com/llm-d/llm-d/releases
  - https://llm-d.ai/docs/architecture/architecture
  - https://github.com/vllm-project/production-stack
  - https://github.com/vllm-project/production-stack/releases
  - https://docs.vllm.ai/en/latest/deployment/integrations/production-stack.html
  - https://github.com/vllm-project/aibrix
  - https://github.com/vllm-project/aibrix/releases
  - https://aibrix.readthedocs.io/latest/getting_started/installation/installation.html
  - https://aibrix.readthedocs.io/latest/designs/aibrix-stormservice.html
  - https://aibrix.readthedocs.io/latest/designs/aibrix-router.html
  - https://aibrix.readthedocs.io/latest/features/autoscaling/metric-based-autoscaling.html
  - https://kthena.volcano.sh/docs/intro
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

This post is based on public information checked as of **2026-05-13**. It is intended for technical reference only. Real-world outcomes depend heavily on workload shape, GPU and network topology, existing control planes, operational maturity, and ecosystem fit. A project's current design should not be treated as its final direction. Community openness, activity, and long-term convergence matter at least as much as any single release.

## TL;DR

The most common mistake in this space is not choosing the wrong project. It is comparing **different layers** as if they were interchangeable:

- `vLLM` and `SGLang` are primarily **runtimes / inference engines**
- `vLLM Production Stack` and `llm-d` are primarily **serving stacks**
- `KServe`, `AIBrix`, `Kthena`, and `Dynamo` are primarily **platforms / control planes**
- `RBG` and `LWS/DisaggregatedSet` are primarily **workload primitives / orchestration APIs**

If you only keep one short decision guide:

- Already deep in `Volcano`: start with `Kthena`
- Already standardized on `KServe`: think `KServe + llm-d`
- Pure `vLLM` team and want the lightest path first: start with `vLLM Production Stack`
- `NVIDIA` cluster and performance system capability is the top priority: start with `Dynamo`
- Want a modular platform on vanilla Kubernetes: start with `AIBrix`
- Already committed to `SGLang`: start with `SGLang Model Gateway`; add `RBG` only if you also need a first-class multi-role Kubernetes workload API

## 1. What changed over the last year

In 2025, this topic was often framed as “everyone is doing PD disaggregation.” In 2026, that framing is no longer enough.

The real convergence is broader:

- the problem is no longer just “how to launch pods”
- `prefill/decode` is no longer just an optimization trick
- the control plane now needs to reason about **roles, routing, KV locality, autoscaling, topology, and failure handling**

Several old assumptions need updating:

- `AIBrix` is no longer just “the KubeRay option.” Its installation guide now explicitly states that `KubeRay` is optional, and `StormService` can run both single-node and multi-node inference without it.
- `Dynamo` should no longer be summarized as “Grove mode vs LWS mode.” Its Kubernetes story is now clearly structured around `DGDR/DGD + Operator + Planner + Grove`.
- `KServe` and `llm-d` should not be treated as mutually exclusive. KServe `0.17` documentation explicitly says `LLMInferenceService` is built on `llm-d`.
- `SGLang` is no longer only a runtime. Its `Model Gateway` now covers routing, Kubernetes service discovery, PD topologies, reliability controls, and Inference Gateway Mode.

## 2. Compare by layer, not by brand name

| Layer | Representative projects | What they are really solving |
| --- | --- | --- |
| Runtime / Engine | `vLLM`, `SGLang` | Efficient execution inside one pod or a tightly scoped serving backend |
| Serving Stack | `vLLM Production Stack`, `llm-d` | Turning runtimes into routable, observable, scalable cluster services |
| Platform / Control Plane | `KServe`, `AIBrix`, `Kthena`, `Dynamo` | Unifying lifecycle, routing, policy, scaling, and operational control |
| Workload Primitive | `RBG`, `LWS/DisaggregatedSet` | Giving Kubernetes a better API for tightly coupled multi-role AI workloads |

This perspective changes the decision entirely:

- if you need a unified entry point and governance model, compare `KServe / AIBrix / Kthena / Dynamo`
- if you need a high-performance distributed serving path, compare `llm-d / vLLM Production Stack / SGLang Gateway`
- if you need a multi-role workload API, compare `RBG / LWS / DisaggregatedSet`

## 3. KServe: a unified AI inference platform, not just a runtime wrapper

As of `2026-05-13`, KServe positions itself as a **Standardized Distributed Generative and Predictive AI Inference Platform**. The most important recent shift is not merely “KServe supports LLMs.” It is that KServe now has a dedicated GenAI path through `LLMInferenceService`.

The `0.17` documentation is explicit:

- `LLMInferenceService` is a dedicated CRD for Generative AI workloads
- it is built on top of `llm-d`
- it exposes multi-node inference, PD separation, advanced routing, and DP+EP patterns at the platform API layer
- it keeps KServe's traditional strengths around lifecycle, unified API, Gateway API integration, and governance

That means many teams should stop asking “KServe or llm-d?” and instead ask:

Should `KServe` be my control plane, and is `llm-d` the distributed serving layer I want under it?

If you already have:

- `Knative` or `KServe` operational experience
- standard Kubernetes API driven model delivery
- a need for shared gateways, quotas, and platform governance

then `KServe + llm-d` is often the most natural path.

## 4. llm-d: a high-performance distributed serving stack

`llm-d` is now much easier to position. It is not a general platform and not just a deployment template for `vLLM`. It is a **Kubernetes-native distributed inference serving stack**.

As of `v0.7.0` on **2026-05-12**, the official release and architecture materials show a fairly complete stack:

- Router and Scheduler as first-class components
- KV cache aware routing
- Prefill/Decode disaggregation
- `LeaderWorkerSet` as a multi-node orchestration path
- variant autoscaling
- integration with the Gateway API inference extension
- a more explicit `SGLang` path in the official guides

Its value is fundamentally about **cluster-wide intelligence**, not just making one runtime pod faster:

- whether requests preserve prefix-cache locality
- whether prefill and decode land in the right resource pools
- whether the router can make better endpoint choices than generic load balancing
- whether tail latency and GPU utilization remain sane under large-model and multi-tenant pressure

If you already know you need:

- cluster-wide cache-aware routing
- role-aware or PD-aware serving
- stronger serving intelligence than `vLLM + Service`

then `llm-d` is one of the clearest options available today.

## 5. vLLM Production Stack: a lighter upstream reference stack

`vLLM Production Stack` should not be understood on the same layer as `llm-d`, `KServe`, or `Dynamo`. Its official README is more modest and more honest: it is **vLLM’s reference system for K8S-native cluster-wide deployment**.

As of `2026-05-07`, the latest release is `vllm-stack-0.1.11`. The current public shape is centered around:

- Helm-based deployment
- a request router
- Prometheus + Grafana observability
- LMCache / KV cache offloading
- scaling from a single vLLM instance to distributed vLLM without changing application code

That makes it attractive in a specific way:

- it is the most natural option for teams already standardized on `vLLM`
- it is thinner and closer to an upstream reference deployment than to a full platform
- it gives you routing, observability, and cache offloading without forcing a larger control-plane adoption up front

Its boundary is equally clear:

- it is not a unified control plane
- it does not aim to provide the governance surface of `KServe / AIBrix / Kthena / Dynamo`
- it is better viewed as a practical starting point than as the final answer to every multi-role orchestration problem

If your question is simply “how do I run an upstream-style vLLM cluster on Kubernetes cleanly?”, this is a very reasonable first stop.

## 6. SGLang and RBG: keep runtime/gateway and workload API separate

These two are often mentioned together, but they solve different layers.

### 6.1 SGLang: a high-performance runtime with an increasingly capable Model Gateway

The current SGLang documentation emphasizes two things at once:

- SGLang is a high-performance serving framework with PD disaggregation, HiCache, multiple parallelism modes, and broad hardware coverage
- SGLang now also has a `Model Gateway` that handles HTTP/gRPC/OpenAI-compatible routing, Kubernetes service discovery, PD topologies, observability, and reliability controls

As of `v0.5.11` on **2026-05-05**, one especially important signal is the continued push toward **Unified Inference Gateway Mode**. That means SGLang is no longer only a runtime. It is also becoming a more complete serving entry point.

If your team is already committed to SGLang, the first decision is often not “which platform should replace it?” but rather:

- use `SGLang` as the runtime
- use `SGLang Model Gateway` to extend it into a manageable fleet entry point

### 6.2 RBG: a multi-role workload primitive

`RBG` does not compete with a gateway. Its value is in `RoleBasedGroup` as a Kubernetes workload API for tightly coordinated distributed inference services.

Its README explicitly highlights:

- role startup-order dependencies
- automated service discovery
- group-level and role-level elastic scaling
- atomic rollout
- topology-aware placement
- atomic failure recovery
- support for multiple role backends, including `StatefulSet`, `Deployment`, and `LeaderWorkerSet`

So the cleaner mental model is:

- `SGLang` solves runtime and gateway
- `RBG` solves how a multi-role inference service is expressed and orchestrated on Kubernetes

If you are already on `SGLang` and feel that plain `Deployment` or `StatefulSet` is too weak for multi-role serving, `RBG` becomes relevant very quickly.

## 7. AIBrix: a modular GenAI infrastructure platform

`AIBrix` is increasingly best understood as a **modular platform**, not a single CRD.

As of `v0.6.0` on **2026-03-03** and the latest official documentation, several signals are clear:

- vanilla Kubernetes is a first-class deployment path
- `Envoy Gateway` is a required entry layer
- `KubeRay` is optional
- `StormService` is a main orchestration path for multi-node inference
- router, KV cache, pod autoscaler, and LoRA-related components all evolve as distinct platform modules

`StormService` itself matters because it is not just a prefill/decode template. It is designed as a three-layer architecture:

- `StormService`
- `RoleSet`
- `Pods`

and it already supports:

- replica mode
- pooled mode
- top-level rolling and inplace update
- RoleSet-level parallel, sequential, and interleaved update strategies

More importantly, the current autoscaling docs explicitly describe **role-level autoscaling in pooled mode**. That is a stronger signal than simply saying “supports PD,” because it reaches the real systems problem: different roles have different load signatures and should not always scale as a single unit.

If your preference is:

- vanilla Kubernetes
- a composable platform
- router, autoscaler, KV, and LoRA management as platform capabilities
- avoiding deep dependence on either `Volcano` or NVIDIA’s full stack

then `AIBrix` is a strong candidate.

## 8. Kthena: a Volcano-native inference control plane

Kthena is no longer a small side effort near Volcano. The `v0.4.0` documentation defines it directly as a **Kubernetes-native AI serving platform**.

Its current value is not just “it also supports PD.” It is that it organizes the following into a coherent service-oriented platform model:

- `ModelBooster`
- `ModelRoute`
- `ModelServer`
- `ModelServing`
- `AutoScalingPolicy`
- `AutoScalingPolicyBinding`

From the current docs and official launch blog, its strengths are clear:

- native affinity with the `Volcano` scheduling ecosystem
- multi-backend support across `vLLM`, `SGLang`, `Triton`, and `TorchServe`
- request-level intelligent routing
- token-based rate limiting, canaries, and failover
- role-aware PD routing
- multi-metric, cost-driven autoscaling

Another important evolution is Kthena’s posture toward LWS. Its public proposal and follow-up PRs show that it is not rejecting `LeaderWorkerSet`. Instead, it is exploring **LWS API compatibility**, treating LWS as one possible northbound interface rather than as the only internal primitive.

If you already stand on:

- `Volcano`
- gang scheduling
- topology-aware placement
- heterogeneous accelerator orchestration

then Kthena is often the most native-feeling answer.

## 9. Dynamo: a performance-system-first inference platform

Dynamo should not be reduced to “an orchestrator.” Its official docs clearly show a broader stack:

- `DynamoGraphDeploymentRequest (DGDR)`: the recommended simplified, SLA-driven entry point
- `DynamoGraphDeployment (DGD)`: a more direct low-level deployment path
- `Planner`
- `Profiler`
- `Router`
- `KVBM`
- multi-node orchestration through `Grove`

The Kubernetes deployment guide and Grove documentation make the current direction explicit:

- the platform layer is centered on `DGDR/DGD + Operator`
- multi-node, multi-role orchestration is primarily handled through `Grove`
- `Planner` helps turn SLA intent into deployment shape and scaling decisions

`Grove` is especially important because it publicly frames itself as:

- a Kubernetes API designed for modern AI workloads, especially disaggregated inference
- a unified way to express prefill, decode, routing, and other components inside one resource
- a path for multi-level horizontal autoscaling, startup dependencies, and topology-aware scheduling

So the more accurate statement today is not “Dynamo has a Grove mode and an LWS mode.” It is:

Dynamo has assembled a broader performance-oriented platform, and `Grove` is the key Kubernetes orchestration path for its multi-role, multi-node serving story.

If your environment is primarily:

- `NVIDIA`
- large-model and multi-node
- strongly SLA-driven
- interested in profiler/planner/backend/KV-path optimization as one system

then `Dynamo` remains especially compelling.

## 10. A more useful comparison table

| Option | Real role | `role / PD` support | Routing / gateway | Scaling | Ecosystem center of gravity |
| --- | --- | --- | --- | --- | --- |
| `KServe` | Unified AI inference platform | Strong, exposed through `LLMInferenceService` | Strong | Strong | Standard Kubernetes platform teams |
| `llm-d` | Distributed serving stack | Very strong | Very strong | Strong | High-performance distributed LLM serving |
| `vLLM Production Stack` | Upstream reference stack | Present but not its most distinctive selling point | Medium to strong | Medium | Pure `vLLM` users |
| `SGLang` | Runtime + gateway | Very strong | Very strong | Medium to strong | `SGLang` runtime users |
| `RBG` | Multi-role workload API | Core capability | Primarily service discovery | Strong | Teams needing a generic multi-role primitive |
| `AIBrix` | Modular GenAI infrastructure platform | Very strong, especially via `StormService / RoleSet` | Strong | Strong, including role-level autoscaling | Vanilla Kubernetes + platform composition |
| `Kthena` | Volcano-native AI serving platform | Very strong, especially via `ModelServing / ServingGroup / Role` | Very strong | Very strong | Volcano / scheduling and topology first |
| `Dynamo` | Performance-first AI infrastructure platform | Very strong, especially via `DGDR/DGD + Grove` | Very strong | Very strong, with planner emphasis | NVIDIA / multi-node / SLA-driven teams |

## 11. How to choose based on your existing infrastructure

The matrix below is intentionally simplified. In real deployments you still need to account for model size, GPU generation, network topology, cost model, platform-team maturity, and multi-tenant boundaries.

### If you are already a Volcano user

Start with `Kthena`.

The point is not just that it supports inference. The point is that it keeps:

- gang scheduling
- topology-aware scheduling
- role-aware inference orchestration
- route/scale/policy control

inside one ecosystem.

### If you are already a KServe user

Start with `KServe + llm-d`, not “KServe or llm-d.”

`KServe` is the control plane. `llm-d` is the distributed serving intelligence. For teams already built around `InferenceService`, Gateway API, and platform governance, this is usually the cleanest next step.

### If you are primarily a vLLM shop

Decide whether you want the lightest path or the most capable serving stack:

- if you want an upstream-style reference deployment first, choose `vLLM Production Stack`
- if you already know you need cache-aware routing, PD, and cluster-level serving intelligence, choose `llm-d`

### If you are primarily an NVIDIA shop

Start with `Dynamo`, especially if you care about:

- multi-node large-model serving
- strong SLA-driven deployment behavior
- using profiler and planner to guide deployment shape
- joint optimization across backend, KV, routing, and orchestration layers

### If you are a vanilla Kubernetes platform team

Start with `AIBrix`.

Its current balance between platform modularity and limited scheduler lock-in is clear. It gives you a natural way to compose:

- `Envoy Gateway`
- `StormService`
- `Router`
- `PodAutoscaler`
- `KV Cache`

without requiring a full shift into either `Volcano` or NVIDIA’s broader stack.

### If you are an SGLang team

The usual progression is:

1. `SGLang runtime`
2. `SGLang Model Gateway`
3. add `RBG` only if you also need a stronger Kubernetes multi-role workload API

In other words, `SGLang` and `RBG` are often complementary rather than substitutes.

### If you want the most upstream-style primitive path

Pay closer attention to:

- `RBG`
- `LWS + DisaggregatedSet`

These matter more as workload APIs than as full inference platforms.

## 12. PD disaggregation is still not the default answer

This point remains true.

Even though nearly every major direction now strengthens `prefill/decode` separation, supporting PD does not mean PD is automatically worth the operational and systems complexity.

PD tends to make the most sense when:

- prompts are long and outputs are relatively short
- concurrency is high and request shapes vary widely
- prefill and decode prefer different hardware or different resource pools
- you truly need to optimize `TTFT` and `TPOT` separately

You should be more cautious when:

- contexts are short or models are small to medium
- concurrency is low
- hardware is homogeneous
- KV transfer and cross-role coordination may erase the gains
- your team does not yet have the observability and operational maturity to support the added moving parts

The real progress today is that platforms are turning PD from a lab technique into an operable system capability. It is still not a free win.

## Conclusion

As of `2026-05-13`, the main story is no longer “who supports PD.” It is “who can turn role-aware orchestration, routing, autoscaling, topology, and failure handling into a system that teams can actually run.”

So the real decision is not only “AIBrix or Kthena or Dynamo.” It is:

- are you choosing a **runtime**, a **serving stack**, a **platform**, or a **workload API**
- do you care more about **ecosystem compatibility** or **performance-system capability**
- do you want to stay close to **upstream generic abstractions** or accept deeper alignment with a stronger ecosystem-specific stack

If you only keep one line:

- want a modular platform: `AIBrix`
- want a Volcano-native inference control plane: `Kthena`
- want a performance-system-first path, especially for NVIDIA: `Dynamo`
- want high-performance distributed serving on Kubernetes: `llm-d`
- want the lightest upstream-style vLLM deployment path first: `vLLM Production Stack`
- already live in the SGLang world: `SGLang Gateway + RBG`
