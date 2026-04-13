---
status: Active
maintainer: pacoxu
last_updated: 2026-04-13
tags: inference, model-serving, kserve, seldon-core, mlops
canonical_path: docs/inference/kserve-seldon-core.md
---

# KServe and Seldon Core: Model Serving Learning Path

This guide focuses on one practical goal: building production-ready model
deployment and serving capability on Kubernetes with KServe and Seldon Core.

## Why This Topic

KServe and Seldon Core are both widely used in Kubernetes-native model serving.
They solve overlapping problems but with different abstractions and operating
models:

- standardizing model deployment APIs
- handling rollout, scaling, and traffic governance
- integrating model runtime, gateway, and observability
- supporting multi-tenant and production operations

## Positioning at a Glance

| Dimension | KServe | Seldon Core |
| --- | --- | --- |
| Core abstraction | `InferenceService` and related serving CRDs | `SeldonDeployment` and serving runtime abstractions |
| Typical fit | Teams that want Kubernetes-native serving APIs and ecosystem alignment | Teams that need flexible runtime composition and strong enterprise MLOps workflows |
| Serving style | Declarative model endpoint management with pluggable runtimes | Graph/pipeline style inference composition and platform integration |
| Scaling path | Native K8s and serverless patterns, plus inference-aware routing ecosystems | Native K8s autoscaling patterns with model-specific runtime controls |

## Core Concept Map

Before deep implementation, align on these concepts:

- Control plane objects: service CRDs, revision/rollout primitives, and traffic
  split policies.
- Data plane execution: model runtimes (vLLM, Triton, custom runtime), batching
  controls, and request backpressure behavior.
- Lifecycle and operations: model versioning, rollback, cold-start/warm-up, and
  autoscaling signals (QPS, queue depth, latency SLO).
- Platform governance: tenant isolation, policy controls, and unified
  observability.

## Entry Learning Path (Weeks 1-4)

### Phase 1: Foundation (Week 1)

- Understand K8s serving essentials: Deployment, Service, Ingress/Gateway, HPA.
- Read KServe and Seldon Core architecture docs end-to-end.
- Define one baseline runtime target (for example vLLM) and one test model.

Deliverable:
- one architecture note comparing both frameworks in your own environment.

### Phase 2: First Deployment (Week 2)

- Deploy KServe in a test cluster and expose one model endpoint.
- Deploy Seldon Core in the same cluster class and expose one equivalent model.
- Validate baseline metrics: availability, P95 latency, error rate, startup time.

Deliverable:
- one reproducible deployment README and minimal load-test report.

### Phase 3: Traffic and Rollout (Week 3)

- Implement canary rollout in both frameworks.
- Test retry/timeout/circuit-break style gateway controls.
- Add rollback runbook for failed model releases.

Deliverable:
- one runbook for release and rollback with objective pass/fail criteria.

### Phase 4: Observability and SLO (Week 4)

- Build model-serving dashboards (latency, success rate, queue depth, cost proxy).
- Add alerting rules for latency regression and error spikes.
- Standardize service-level SLI/SLO definitions across both frameworks.

Deliverable:
- one shared observability dashboard and one alert policy set.

## Deep-Dive Learning Path (Weeks 5-10)

### Phase 5: Multi-Tenant Governance

- Per-tenant quota and priority isolation.
- Namespace-level policy controls and network boundaries.
- Cost attribution by model, tenant, and environment.

### Phase 6: Performance Engineering

- Tune concurrency, batching, and autoscaling thresholds.
- Compare cold-start mitigation patterns (prewarm, cache, image/model loading path).
- Analyze bottlenecks with profiling and request-path tracing.

### Phase 7: Advanced Serving Patterns

- Multi-model routing and model gateway policy design.
- A/B testing and shadow traffic for safe validation.
- Pipeline/graph inference patterns for composite model services.

### Phase 8: Production Readiness

- Progressive delivery gates in CI/CD.
- Failure injection and recovery drills.
- Security and compliance checks for model artifacts and endpoints.

## Suggested Hands-On Projects

1. Framework parity PoC: deploy the same model on KServe and Seldon Core, then
   produce side-by-side latency and stability comparison.
2. Safe release pipeline: build CI/CD flow with canary, automated checks, and
   rollback trigger.
3. Multi-tenant serving blueprint: define one reference architecture for two
   tenants with separate SLO and quota.
4. Performance and cost baseline: establish repeatable benchmark protocol and
   monthly regression checks.

## Completion Criteria

- Team can deploy and rollback models on both frameworks without manual ad-hoc
  steps.
- SLI/SLO dashboard is unified and actionable.
- There is a written framework selection guide for your environment
  (when to use KServe, when to use Seldon Core, and when mixed mode is needed).
- At least one production-like drill validates failure recovery and release
  safety.

## Related Docs in This Repo

- [Inference Overview](./README.md)
- [Performance Testing & Benchmark Tools](./performance-testing.md)
- [Serverless AI Inference](./serverless.md)
- [Model Lifecycle Management](./model-lifecycle.md)
- [Caching in LLM Inference](./caching.md)

## External References

- [KServe Project](https://github.com/kserve/kserve)
- [KServe Documentation](https://kserve.github.io/website/)
- [Seldon Core Project](https://github.com/SeldonIO/seldon-core)
- [Seldon Documentation](https://docs.seldon.ai/)
