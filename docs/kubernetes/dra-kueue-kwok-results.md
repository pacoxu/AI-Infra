---
status: Active
maintainer: pacoxu
last_updated: 2026-08-13
tags: kubernetes, dra, kueue, kwok, benchmark-results
canonical_path: docs/kubernetes/dra-kueue-kwok-results.md
---

# DRA + Kueue KWOK-only results

The KWOK-only acceptance run completed on 2026-08-13. Functional and scale
profiles each completed three rounds, and the per-profile and combined
`verify` commands all passed. The publishable artifacts are under
[`20260813T063105Z`](./dra-kueue-kwok-results-data/20260813T063105Z/).

> All values in this report represent KWOK control-plane behavior only. They
> cannot be interpreted as real GPU startup, allocation, health, or workload
> performance.

## Acceptance status

| Profile | Nodes | Simulated devices | Logical workloads per round | Completed rounds | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Functional | 10 | 80 | 100 | 3 | PASS |
| Scale | 100 | 800 | 1000 | 3 | PASS |

All runs used Kubernetes `v1.36.3`, KWOK `v0.8.0`, and Kueue `v0.19.0`.
There were 5,310 workload records: 495 functional and 4,815 scale, including
the direct controls, Extended Resource smoke, and failure cases. All 3,300 main
Workloads succeeded.

## End-to-end acceptance

Short jobs use deterministic 20-Job waves for both the direct and Kueue paths.
Each wave reaches Ready before the next wave, while all 60 or 600 short jobs
still execute in every round. This is the high-churn comparison model; it
prevents API creation burst tail latency from being attributed only to Kueue.

| Profile | Round | Direct P50/P95/P99 | Kueue P50/P95/P99 | P95 increment | Idle with admitted pending | Main success |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| Functional | 1 | 0/0/0s | 1/1/1s | 1s | 1.55% | 100% |
| Functional | 2 | 0/1/1s | 0/1/1s | 0s | 1.58% | 100% |
| Functional | 3 | 0/1/1s | 0/1/1s | 0s | 1.63% | 100% |
| Scale | 1 | 0/1/1s | 1/1/1s | 0s | 1.66% | 100% |
| Scale | 2 | 0/1/1s | 1/2/2s | 1s | 2.12% | 100% |
| Scale | 3 | 0/1/1s | 1/2/2.01s | 1s | 1.65% | 100% |

Every P95 increment is below the 3-second effective limit, and every idle
ratio is below 15%. End-to-end P95 CV was 0% for functional and 28.28% for
scale. Admission P95 CV was 0% and 17.61%, respectively; all acceptance CVs
are below 30%.

## Lifecycle and queue evidence

| Profile | Round | Admission P50/P95/P99 | Claim allocate P50/P95/P99 | Pod schedule P50/P95/P99 | Preemptions | Max weighted share A/B |
| --- | ---: | --- | --- | --- | ---: | --- |
| Functional | 1 | 0/1/1s | 0.72/1.65/1.72s | 0/0.01/0.20s | 6 | 125/125 |
| Functional | 2 | 0/1/1s | 1.02/2.06/2.06s | 0/0.12/0.12s | 4 | 125/125 |
| Functional | 3 | 0/1/1s | 0.97/1.98/2.43s | 0/0.02/0.03s | 6 | 125/125 |
| Scale | 1 | 0/12/15s | 0.90/18.89/20.81s | 0/0.92/1.24s | 8 | 125/125 |
| Scale | 2 | 0/14/17s | 1.04/26.37/27.37s | 0/1.17/1.89s | 10 | 125/125 |
| Scale | 3 | 0/9/10s | 0.82/11.83/13.70s | 0/1.17/1.42s | 12 | 125/125 |

Claim create, allocation, reservation, PodScheduled, simulated Ready, owner
deletion, Claim deletion, and quota release are present for every successful
main and direct workload. Reclaim evidence is read from both sampled Workload
conditions and durable Kubernetes Events, so a transient `Evicted=True`
condition cannot be lost between collector polls.

The scale subinterval CVs for Claim create and allocation exceed 30%, but these
are reported diagnostics rather than the selected critical gates. The accepted
critical CVs are Kueue end-to-end P95 and admission P95, matching the stated
three-round acceptance contract.

## Reproduce and inspect

Follow the [PoC runbook](./dra-kueue-kwok-poc.md#run-both-acceptance-profiles).
Machine-readable details are in
[`summary.json`](./dra-kueue-kwok-results-data/20260813T063105Z/summary.json),
with the generated [`report.md`](./dra-kueue-kwok-results-data/20260813T063105Z/report.md).
No required scenario was skipped.

## Failure attribution vocabulary

| Scenario | Expected evidence |
| --- | --- |
| Quota insufficient | `ExceedsMaxQuota`; never QuotaReserved; quota is zero after deletion |
| No matching ResourceSlice | admitted; `cannot allocate all claims`; WaitForPodsReady eviction and requeue |
| Admitted but unschedulable | admitted; PodScheduled=False due to node selector; eviction and requeue |
| WaitForPodsReady | two timeout evictions, two requeues, 5/10-second backoff evidence |

All four cases produced the expected failure/requeue behavior in all six
rounds and released quota after deletion. The observed scheduler reasons
included `cannot allocate all claims` and impossible node-selector diagnostics.

## Collection limitation

All six kube-scheduler metric snapshots are present and non-empty. KWOK 0.8.0
turns Kueue Services into port-less ExternalNames and does not expose the
controller metrics port, so `kueue-metrics.prom` is empty by design in this
pinned environment. Kueue logs, Kubernetes Events, queue snapshots,
pending-reason API output, weighted shares, and object-derived lifecycle
metrics are retained instead.

## Consumer boundary

Issue #363 may consume queue, quota, requeue, scale, weighted-share, and
pending-reason baselines. It must not claim cross-cluster real-device readiness
from these results.
