---
status: Active
maintainer: pacoxu
last_updated: 2026-10-04
tags: inference, conformance, preflight, llm, slo
canonical_path: docs/inference/inference-conformance.md
---

# Inference Conformance and Preflight Gate

Use this engine-neutral checklist before promoting an LLM service. The
preflight script in [`scripts/conformance/preflight.sh`](../../scripts/conformance/preflight.sh)
exercises an OpenAI-compatible chat endpoint and evaluates an externally
collected metrics snapshot. It is a small release gate, not a benchmark or a
replacement for production monitoring.

## Gate policy

| Gate | Requirement | Pass condition |
| --- | --- | --- |
| Smoke | **Required** | One representative request succeeds, returns valid output, and responds with a successful HTTP status. |
| Load | **Required** | The configured request sample completes without errors and meets the configured minimum successful request rate. Use a dedicated load tool for concurrency and realistic traffic shapes. |
| SLO | **Required** | A fresh metrics snapshot contains all required measurements and every configured threshold passes. |
| Rollback | **Required** | A supplied, read-only rollback readiness check succeeds before promotion. On a failed gate after deployment, follow the rollback checklist below; the script does not change production traffic or roll back automatically. |
| Quality, resilience, and capacity extensions | Recommended | Add model-specific quality checks, failure injection, concurrency ramps, autoscaling, and longer soak tests appropriate to the risk. |

Run gates against an isolated candidate or canary. Do not send synthetic load
to an unapproved production service. A failed required gate blocks promotion.

## Conformance dimensions

| Dimension | Required checks | Recommended checks |
| --- | --- | --- |
| Model and artifacts | Model ID/revision, tokenizer, quantization, context length, and artifact digest match the release manifest; a representative prompt returns a non-empty completion. | Compare a fixed quality/evaluation set with the approved baseline; exercise model switching and warm-up. |
| Runtime | Ready replicas expose the expected API and model; startup completes within the deployment deadline; runtime configuration and image are pinned. | Test graceful shutdown, OOM recovery, batching, speculative decoding, and a cold start. |
| Router and rollout | The routed endpoint reaches the candidate and reports request errors; auth, timeout, retry, and traffic-split policies are correct. | Verify sticky/session routing, health-based failover, rate limits, and canary isolation. |
| GPU and capacity | Expected accelerator type/count is allocated; no persistent GPU error or out-of-memory event; capacity has headroom at the target load. | Check GPU utilization, memory bandwidth, power/thermal state, fragmentation, and autoscaling behavior. |
| KV cache | Cache usage and hit-rate measurements are present; cache pressure remains within the workload's approved limit. | Test prefix reuse, eviction, cache isolation, offload, and correctness after model or adapter switching. |
| Metrics and SLO | Collect TTFT, TPOT, ITL, goodput, GPU cache usage, KV hit rate, request errors, and a time window/sample count. The SLO gate checks the six values in the threshold template below. | Break down by model, prompt/output length, replica, tenant, and cache-hit status; alert on saturation and error budgets. |
| Recovery | A known-good revision/artifact exists and the rollback readiness check can resolve the rollback target. | Rehearse traffic rollback and verify data/config compatibility and recovery time in staging. |

### Metrics and example thresholds

Use these as a template, not universal SLOs. Set thresholds from the product
SLO, workload mix, model, hardware, and a representative baseline. Values in
the table are examples only; the script environment-variable defaults are
intentionally permissive except for basic latency ceilings.

| Metric | Definition for the gate | Example threshold | Direction |
| --- | --- | --- | --- |
| TTFT P95 (ms) | Time from request acceptance to first generated token; exclude queueing only if the product SLO does. | 1,000 | Maximum |
| TPOT P95 (ms/token) | Mean per-output-token time after the first token, calculated per request before taking P95. | 100 | Maximum |
| ITL P95 (ms) | P95 interval between adjacent generated tokens. | 150 | Maximum |
| Goodput (output tokens/s) | Output tokens per second delivered while requests meet the latency and error SLOs. | 100 | Minimum |
| GPU cache usage (%) | Peak or sustained KV/GPU cache occupancy over the same load window; document which aggregation is used. | 90 | Maximum |
| KV hit rate (%) | Cache hits divided by cache lookups over the same workload window. | 20 | Minimum |

`METRICS_FILE` is JSON supplied by the deployment's metrics adapter, with
numeric values named `ttft_p95_ms`, `tpot_p95_ms`, `itl_p95_ms`,
`goodput_tokens_per_sec`, `gpu_cache_usage_pct`, and `kv_hit_rate_pct`.
Capture them from the same representative load window, after warm-up, and
include the scrape interval and sample count in release evidence. Metric names
and labels differ between engines; map the engine's Prometheus series into
this small common shape rather than assuming identical names or semantics.

The preflight script times serial HTTP requests for its minimal load gate.
Those request times are not token-level TTFT, TPOT, or ITL. Use a streaming
benchmark or telemetry adapter for those measurements; do not populate the
SLO snapshot from the serial request timer. The load gate's request rate is
also not a substitute for token goodput.

## Run the minimum preflight

Requirements: Bash, `curl`, and `jq`. The endpoint must implement the
OpenAI-compatible `POST /v1/chat/completions` API. Configure a fresh metrics
snapshot and a trusted read-only command that verifies the known-good revision
and rollback mechanism. The rollback check command is run with `bash -c`; do
not set it from untrusted input.

```bash
export BASE_URL=https://candidate.example.com
export MODEL=my-model
# export API_KEY=your-token # omit when the endpoint does not require authentication
export METRICS_FILE=./candidate-metrics.json
export ROLLBACK_CHECK_CMD='kubectl get deployment/my-model -o json | jq -e ".metadata.annotations.rollbackRevision"'
export LOAD_REQUESTS=10
export LOAD_MIN_REQUESTS_PER_SEC=0.5
export TTFT_P95_MAX_MS=1000
export TPOT_P95_MAX_MS=100
export ITL_P95_MAX_MS=150
export GOODPUT_MIN_TOKENS_PER_SEC=100
export GPU_CACHE_USAGE_MAX_PCT=90
export KV_HIT_RATE_MIN_PCT=20

bash scripts/conformance/preflight.sh
```

The rollback command above is only an example: adapt it to the platform and
ensure it verifies the actual previous known-good revision. It must be
read-only; the script never executes a rollback.

| Outcome | Example | Expected result |
| --- | --- | --- |
| Success path | A healthy candidate returns completions, the load sample passes, all six snapshot values meet thresholds, and the rollback readiness command exits 0. | Script exits 0 and prints `Preflight passed`. |
| Failure path | Set `TTFT_P95_MAX_MS=1` with a metrics snapshot whose `ttft_p95_ms` is 100. | Script exits non-zero at the SLO gate, prints the failed measurement, and promotion is blocked. Use the rollback checklist if the candidate already received traffic. |

## Engine and platform adapters

Keep gate outcomes common and implement collection in the native runtime,
router, or platform adapter:

| System | Adapter-specific evidence |
| --- | --- |
| vLLM | OpenAI-compatible health/completion endpoint; model and engine arguments; vLLM request, latency, and `vllm:gpu_cache_usage_perc` metrics. |
| SGLang | OpenAI-compatible endpoint and model/runtime configuration; scheduler, cache, and token-latency metrics from its exporter. |
| TensorRT-LLM | Triton or the deployed frontend's endpoint; engine/build compatibility, model repository readiness, and GenAI/Triton metrics. |
| KServe | `InferenceService`/`LLMInferenceService` readiness, predictor health, revision/traffic split, and the routed endpoint rather than only an internal pod. |
| AIBrix | Gateway route and model identity, routing/cache behavior, `StormService`/replica readiness, and gateway plus engine metrics. |
| llm-d | KServe ingress, routing/connector readiness, prefill/decode roles, KV transfer health, and role-level metrics. |

The universal checks are the observable contract: intended model and version,
serving endpoint, valid response, measured workload, common SLO fields, and
recoverable release. Verify additional native health and metrics at the
component boundary; do not assume an endpoint smoke test proves the control
plane, router, or engine is healthy.

## P/D disaggregation and multi-node additions

These checks are **required when the deployment uses P/D disaggregation or
multiple nodes**:

- Verify every prefill and decode role has the expected replica count, model
  revision, resources, and readiness before sending traffic.
- Send requests through the production-intended router and prove prefill
  output reaches decode. Check routing, KV transfer/connector errors, timeout,
  retries, and cancellation behavior.
- Measure end-to-end TTFT and TPOT as well as role-level queueing and service
  times. Check KV transfer latency, throughput, failures, cache usage, and
  cache-hit rate; the combined system must meet the same user-facing SLO.
- Confirm nodes can communicate over the expected network/topology and
  transport (for example RDMA/NIXL where configured). Validate placement,
  gang/startup ordering, peer discovery, and failure handling for a lost node
  or role.
- Test scaling and rollout with role-aware capacity: no partial rollout that
  leaves an unusable role set, and the previous complete revision remains
  available for rollback.

For single-node, non-disaggregated serving these checks are not applicable;
record that scope in the release evidence.

## Failure handling and rollback checklist

1. **Block promotion** on any required gate failure. Record the candidate
   revision, workload, metric snapshot/window, threshold, failed check, and
   logs. Do not hide missing metrics by treating them as zero.
2. **Classify and contain** the issue: model/artifact, runtime, router,
   accelerator/capacity, KV cache, or P/D/network. Stop the load generator and
   keep canary traffic isolated.
3. **If the candidate is already serving traffic**, shift traffic to the
   previous known-good revision using the platform's tested procedure
   (KServe traffic split, gateway route, or deployment revision). The script
   does not execute this action.
4. Verify the prior revision serves a smoke request, errors and latency return
   within SLO, and GPU/cache resources recover. For P/D, verify the complete
   previous prefill/decode set and router/KV path, not just one role.
5. Preserve evidence, notify the owner, and open a follow-up with remediation
   and a repeatable regression check. Retry promotion only after required
   gates pass on a fresh snapshot and rollback readiness is re-verified.

## Related documentation

- [Performance testing and benchmark tools](./performance-testing.md)
- [Prefill-Decode disaggregation](./pd-disaggregation.md)
- [Caching in LLM inference](./caching.md)
- [Model lifecycle management](./model-lifecycle.md)
