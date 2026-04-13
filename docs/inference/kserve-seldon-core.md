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

## Capability, Complexity, and Ops Cost Matrix

Use this matrix as a first-pass decision baseline:

| Area | KServe | Seldon Core | Notes |
| --- | --- | --- | --- |
| Single model endpoint | Strong | Strong | Both are production-capable |
| Multi-model routing and composition | Medium to strong | Strong | Seldon graph/pipeline patterns are often preferred for complex compositions |
| Kubernetes ecosystem alignment | Strong | Medium to strong | KServe often fits teams optimizing for Kubernetes-native serving APIs |
| Day-2 operations complexity | Medium | Medium to high | Complexity depends on runtime mix and policy depth |
| Governance and enterprise controls | Medium to strong | Strong | Seldon often appears in stricter enterprise governance scenarios |
| Team onboarding speed | Strong | Medium | KServe onboarding can be simpler for K8s-native teams |

## Minimal Deployment Templates (MVP)

The goal is repeatability, not framework-specific optimization. Start with one
model and one runtime, then expand.

### KServe MVP Template

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sample-kserve-model
  namespace: inference
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: "s3://model-bucket/sklearn-iris"
```

### Seldon Core MVP Template

```yaml
apiVersion: machinelearning.seldon.io/v1
kind: SeldonDeployment
metadata:
  name: sample-seldon-model
  namespace: inference
spec:
  name: sample
  predictors:
  - name: default
    replicas: 1
    graph:
      name: classifier
      implementation: SKLEARN_SERVER
      modelUri: "s3://model-bucket/sklearn-iris"
      endpoint:
        type: REST
```

If you use newer Seldon runtime stacks, keep the same validation flow but adapt
CRDs and runtime fields accordingly.

## Unified Benchmark and Observability Baseline

Define one common benchmark protocol before framework comparison:

| Category | Baseline |
| --- | --- |
| Workload profiles | low concurrency, burst traffic, sustained traffic |
| Latency | p50, p95, p99 |
| Reliability | success rate, timeout rate, 5xx rate |
| Throughput | requests per second, tokens per second (for LLM) |
| Efficiency | CPU, memory, GPU utilization, queue depth |
| Startup | cold-start duration, first-request latency |
| Cost proxy | cost per 1k requests or cost per token |

Recommended report output:

1. Environment and runtime config snapshot.
2. Traffic profile definition.
3. Side-by-side KServe vs Seldon Core results table.
4. Top bottlenecks and remediation suggestions.

## Release and Rollback Runbook (Minimum)

- Pre-release checks: config lint/schema validation, dependency and model
  artifact readiness, baseline smoke tests.
- Progressive release: start with canary traffic split, monitor p95 and error
  rate, then increase traffic only when SLO remains stable.
- Rollback triggers: sustained error-rate increase, p95/p99 latency regression,
  or persistent queue backlog growth.
- Rollback actions: route traffic to the previous stable revision, verify
  recovery, then create a postmortem with guardrail updates.

## Framework Selection Guidance

| Scenario | Recommendation |
| --- | --- |
| Fast Kubernetes-native standardization with moderate complexity | Prefer KServe |
| Complex inference graph and stronger enterprise MLOps controls | Prefer Seldon Core |
| Mixed organization with different workload classes | Hybrid mode (KServe + Seldon Core), but unify SLO and observability |
| Team has limited platform capacity | Start with one framework first, avoid dual-stack in early phase |

Risks to track for any choice:

- fragmented runtime configurations across teams
- inconsistent SLI/SLO definitions
- no clear rollback ownership
- benchmark results not reproducible

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
