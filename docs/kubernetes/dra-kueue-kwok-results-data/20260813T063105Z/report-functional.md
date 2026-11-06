# DRA + Kueue KWOK-only results

Generated at `2026-08-13T08:20:35.060144Z` by `poc.sh collect`.

> These measurements represent KWOK control-plane behavior only. They do not
> measure real GPU initialization, DRA node plugins, CDI, DCGM, or workload performance.

Overall acceptance: **PASS**

| Profile | Round | Main success | Direct P95 | Kueue P95 | Increment | Idle with admitted pending | Preemptions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| functional | 1 | 100.00% | 0.000s | 1.000s | 1.000s | 1.55% | 6 |
| functional | 2 | 100.00% | 1.000s | 1.000s | 0.000s | 1.58% | 4 |
| functional | 3 | 100.00% | 1.000s | 1.000s | 0.000s | 1.63% | 6 |

| Round | Lifecycle interval | P50 | P95 | P99 | Samples |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `queue_wait` | 0.000s | 1.000s | 1.000s | 100 |
| 1 | `admission` | 0.000s | 1.000s | 1.000s | 100 |
| 1 | `claim_create` | 0.000s | 1.000s | 1.000s | 100 |
| 1 | `claim_allocate` | 0.717s | 1.649s | 1.720s | 100 |
| 1 | `pod_schedule` | 0.000s | 0.007s | 0.201s | 100 |
| 1 | `simulated_ready` | 0.000s | 0.000s | 1.000s | 100 |
| 1 | `claim_reclaim` | 0.000s | 0.000s | 0.000s | 100 |
| 2 | `queue_wait` | 0.000s | 1.000s | 1.000s | 100 |
| 2 | `admission` | 0.000s | 1.000s | 1.000s | 100 |
| 2 | `claim_create` | 0.000s | 1.000s | 1.000s | 100 |
| 2 | `claim_allocate` | 1.025s | 2.062s | 2.062s | 100 |
| 2 | `pod_schedule` | 0.000s | 0.116s | 0.116s | 100 |
| 2 | `simulated_ready` | 0.000s | 0.000s | 1.000s | 100 |
| 2 | `claim_reclaim` | 0.000s | 0.000s | 0.000s | 100 |
| 3 | `queue_wait` | 0.000s | 1.000s | 1.000s | 100 |
| 3 | `admission` | 0.000s | 1.000s | 1.000s | 100 |
| 3 | `claim_create` | 0.000s | 1.000s | 1.000s | 100 |
| 3 | `claim_allocate` | 0.968s | 1.983s | 2.430s | 100 |
| 3 | `pod_schedule` | 0.000s | 0.018s | 0.032s | 100 |
| 3 | `simulated_ready` | 0.000s | 1.000s | 1.000s | 100 |
| 3 | `claim_reclaim` | 0.000s | 0.000s | 0.000s | 100 |

## functional P95 CVs

- `kueue_end_to_end_p95`: 0.00%
- `queue_wait_p95`: 0.00%
- `admission_p95`: 0.00%
- `claim_create_p95`: 0.00%
- `claim_allocate_p95`: 9.43%
- `pod_schedule_p95`: 104.17%
- `simulated_ready_p95`: 141.42%
- `claim_reclaim_p95`: 0.00%

## Consumer boundary for #363

Issue #363 may consume queue, quota, requeue, scale, and pending-reason baselines.
It must not use this report as evidence that real devices are prepared across clusters.
