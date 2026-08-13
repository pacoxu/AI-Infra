# DRA + Kueue KWOK-only results

Generated at `2026-08-13T07:52:12.442123Z` by `poc.sh collect`.

> These measurements represent KWOK control-plane behavior only. They do not
> measure real GPU initialization, DRA node plugins, CDI, DCGM, or workload performance.

Overall acceptance: **PASS**

| Profile | Round | Main success | Direct P95 | Kueue P95 | Increment | Idle with admitted pending | Preemptions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| scale | 1 | 100.00% | 1.000s | 1.000s | 0.000s | 1.66% | 8 |
| scale | 2 | 100.00% | 1.000s | 2.000s | 1.000s | 2.12% | 10 |
| scale | 3 | 100.00% | 1.000s | 2.000s | 1.000s | 1.65% | 12 |

| Round | Lifecycle interval | P50 | P95 | P99 | Samples |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `queue_wait` | 0.000s | 12.000s | 15.000s | 1000 |
| 1 | `admission` | 0.000s | 12.000s | 15.000s | 1000 |
| 1 | `claim_create` | 0.000s | 7.000s | 8.000s | 1000 |
| 1 | `claim_allocate` | 0.898s | 18.894s | 20.814s | 1000 |
| 1 | `pod_schedule` | 0.000s | 0.918s | 1.245s | 1000 |
| 1 | `simulated_ready` | 0.000s | 1.000s | 1.000s | 1000 |
| 1 | `claim_reclaim` | 0.000s | 0.000s | 4.373s | 1000 |
| 2 | `queue_wait` | 0.000s | 14.000s | 17.000s | 1000 |
| 2 | `admission` | 0.000s | 14.000s | 17.000s | 1000 |
| 2 | `claim_create` | 0.000s | 14.000s | 15.000s | 1000 |
| 2 | `claim_allocate` | 1.044s | 26.372s | 27.372s | 1000 |
| 2 | `pod_schedule` | 0.000s | 1.169s | 1.891s | 1000 |
| 2 | `simulated_ready` | 0.000s | 1.000s | 4.000s | 1000 |
| 2 | `claim_reclaim` | 0.000s | 0.000s | 2.774s | 1000 |
| 3 | `queue_wait` | 0.000s | 9.000s | 10.000s | 1000 |
| 3 | `admission` | 0.000s | 9.000s | 10.000s | 1000 |
| 3 | `claim_create` | 0.000s | 4.000s | 5.000s | 1000 |
| 3 | `claim_allocate` | 0.816s | 11.833s | 13.695s | 1000 |
| 3 | `pod_schedule` | 0.000s | 1.167s | 1.420s | 1000 |
| 3 | `simulated_ready` | 0.000s | 1.000s | 1.000s | 1000 |
| 3 | `claim_reclaim` | 0.000s | 0.000s | 3.766s | 1000 |

## scale P95 CVs

- `kueue_end_to_end_p95`: 28.28%
- `queue_wait_p95`: 17.61%
- `admission_p95`: 17.61%
- `claim_create_p95`: 50.28%
- `claim_allocate_p95`: 31.19%
- `pod_schedule_p95`: 10.86%
- `simulated_ready_p95`: 0.00%
- `claim_reclaim_p95`: 0.00%

## Consumer boundary for #363

Issue #363 may consume queue, quota, requeue, scale, and pending-reason baselines.
It must not use this report as evidence that real devices are prepared across clusters.
