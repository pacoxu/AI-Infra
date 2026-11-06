---
status: Active
maintainer: pacoxu
last_updated: 2026-08-13
tags: kubernetes, dra, kueue, kwok, scheduling, benchmarking
canonical_path: docs/kubernetes/dra-kueue-kwok-poc.md
---

# DRA + Kueue KWOK-only control-plane PoC

This is the reproducible baseline for [AI-Infra #285](https://github.com/pacoxu/AI-Infra/issues/285).
It intentionally validates control-plane behavior only.

> Results from this harness do not measure real GPU startup, device
> initialization, a DRA node plugin, CDI, DCGM, or training and inference
> performance.

## Scope and fixed versions

| Component | Version | Enforcement |
| --- | --- | --- |
| Kubernetes server | `v1.36.3` | `setup` and `run` compare the exact server version |
| KWOK / `kwokctl` | `v0.8.0` | exact binary and controller image in generated config |
| Kueue | `v0.19.0` | exact release manifest and running image preflight |

The main path uses `resource.k8s.io/v1` `ResourceClaimTemplate`,
`ExactCount`, and Kueue `deviceClassMappings`. The Extended Resource path is
one compatibility smoke test. The harness never emits the old DRA `v1beta1`
API shown in the older [KWOK DRA example](https://kwok.sigs.k8s.io/docs/examples/dra/).

TAS is intentionally absent. Kueue 0.19 does not include DRA resources in TAS
capacity calculations; see the
[Kueue 0.19 DRA boundary](https://kueue.sigs.k8s.io/v0.19/docs/concepts/dynamic_resource_allocation/).

## Model

Each KWOK node owns one `ResourceSlice` with eight non-shareable simulated
devices. The functional profile has 10 nodes and 80 devices; the scale profile
has 100 nodes and 800 devices.

Tenant A and tenant B each have one `LocalQueue` and `ClusterQueue`. Both
ClusterQueues join the same cohort, receive 50% nominal GPU quota, and use a
fair-sharing weight of `1`. Preemption is configured as:

```yaml
withinClusterQueue: LowerPriority
reclaimWithinCohort: Any
```

The low-priority tenant A workload has priority `-100`, normal steady workloads
have priority `0`, and the tenant B owner workload has priority `1000`. This
ensures the observed sequence is borrowing from tenant B followed by owner
reclaim, rather than within-queue preemption.

`WaitForPodsReady` uses a 60-second timeout, 30-second recovery timeout, two
backoff-limited requeues, and a 5-to-20-second backoff. KWOK stages leave Jobs
and Deployments Running until the harness deletes them, which provides a stable
sampling window and deterministic Claim garbage-collection evidence.

## Prerequisites

- Docker daemon
- `kubectl`, `curl`, `jq`, `rg`, and Python 3
- Internet access on the first run to fetch exact release artifacts or build
  `kwokctl`; cached artifacts are reused afterward

The local `kubectl` may print a version-skew warning if it is older than the
fixed server. The server itself must still be exactly `v1.36.3`.

## Run both acceptance profiles

Choose a new output directory for every acceptance run. Existing JSONL output
is never silently overwritten.

```bash
OUTPUT="docs/kubernetes/dra-kueue-kwok-results-data/$(date -u +%Y%m%dT%H%M%SZ)"

scripts/dra-kueue-kwok/poc.sh setup \
  --profile functional --rounds 3 --output "${OUTPUT}"
scripts/dra-kueue-kwok/poc.sh run \
  --profile functional --rounds 3 --output "${OUTPUT}"
scripts/dra-kueue-kwok/poc.sh collect \
  --profile functional --rounds 3 --output "${OUTPUT}"
scripts/dra-kueue-kwok/poc.sh verify \
  --profile functional --rounds 3 --output "${OUTPUT}"

scripts/dra-kueue-kwok/poc.sh setup \
  --profile scale --rounds 3 --output "${OUTPUT}"
scripts/dra-kueue-kwok/poc.sh run \
  --profile scale --rounds 3 --output "${OUTPUT}"
scripts/dra-kueue-kwok/poc.sh collect \
  --profile scale --rounds 3 --output "${OUTPUT}"
scripts/dra-kueue-kwok/poc.sh verify \
  --profile scale --rounds 3 --output "${OUTPUT}"
```

Do not replace a required phase with `SKIP`. The scale setting is a logical
workload count: a four-Pod training Job and a two-replica Deployment each count
as one of the 100 or 1000 logical workloads.

## Workload and failure coverage

Every round contains the following logical workload proportions:

| Scenario | Share | Object | Purpose |
| --- | ---: | --- | --- |
| Short | 60% | one-Pod Job | churn, admission, allocation, and Claim GC |
| Long training model | 10% | four-Pod Job | sustained quota and device use |
| Quasi-online inference | 10% | two-replica Deployment | stable Ready window |
| Mixed contention | 20% | two-replica Deployment | borrow, reclaim, preemption, starvation |

The same short-job DRA model is also submitted without Kueue as the relative
control. Direct and Kueue short jobs use identical deterministic 20-Job waves;
each wave reaches Ready before the next one. All 60 or 600 short jobs still run
in each round, and the wave model measures sustained high churn without
charging a one-time 600-object API creation burst exclusively to Kueue. Four
failure cases are additional and do not count toward the profile total: quota
beyond cohort capacity, a DeviceClass without a matching slice, an admitted
Pod with an impossible node selector, and two WaitForPodsReady timeout/requeue
cycles.

## Data and acceptance contract

Each round writes `workloads.jsonl`, `events.jsonl`, `samples.jsonl`, generated
manifests, Kubernetes events, queue snapshots, scheduler metrics, and Kueue and
scheduler logs. KWOK 0.8 turns Kueue Services into port-less ExternalNames, so
direct Kueue metrics are unavailable in this pinned runtime; the collector
derives queue wait and weighted share from Kueue objects and lifecycle events.
A logical workload record includes creation, QuotaReserved,
Admitted, Claim create/allocation/reservation/deletion, PodScheduled, simulated
Ready, owner deletion, quota release, final reason, and final result.

`verify` fails unless all required lifecycle and scenario counts are present,
the Extended Resource smoke passes, preemption is observed through a sampled
condition or a durable Kubernetes Event within the mixed workload lifetime,
every failure releases quota, and these thresholds hold:

- Kueue short-job end-to-end P95 increment is at most `max(25%, 3s)` over the
  direct path.
- Simulated device idle time attributable to admitted pending demand is at most
  15% of total capacity.
- Cross-round CV for Kueue end-to-end P95 and admission P95 is at most 30%.

The aggregate report contains P50/P95/P99 for queue wait, admission, Claim
creation/allocation/reclaim, Pod scheduling, and simulated Ready intervals.

## Troubleshooting

| Symptom | Check | Action |
| --- | --- | --- |
| Exact server check fails | `kubectl version -o json` using the generated kubeconfig | Run `setup`; never lower the expected version |
| Required API is absent | `kubectl api-versions` | Confirm the fixed Kubernetes/Kueue images and recreate the PoC cluster |
| Pod is admitted but Pending | scheduler log, PodScheduled=False, Claim allocation | Confirm ResourceSlice node and DeviceClass mapping; failure scenarios expect this state |
| Claim remains allocated | owner, Pod, and Workload deletion events | Preserve the round output, then run `cleanup`; treat missing GC evidence as a failed round |
| Owner reclaim is absent | ClusterQueue `flavorsReservation`, workload priorities | Verify `-100 < 0 < 1000` and tenant A borrowed GPU quota before owner submission |
| WaitForPodsReady does not requeue twice | Kueue events and `evictions`/`requeues` fields | Allow the complete 155-second failure window |

## Cleanup and rollback

```bash
scripts/dra-kueue-kwok/poc.sh cleanup \
  --profile scale --rounds 3 --output "${OUTPUT}"
```

Cleanup deletes the isolated KWOK cluster and verifies that no test namespace,
Queue, `ResourceSlice`, `ResourceClaim`, or Workload remains. Raw result files
are preserved. The PoC has no production-cluster install or rollback path;
never repoint its generated kubeconfig at another cluster.

## Boundary for #363 MultiKueue

Issue #363 may consume the queue, cohort quota, fair-sharing, borrow/reclaim,
preemption, requeue, scale, and pending-reason baselines. It must not interpret
them as evidence that a remote cluster has a working DRA node plugin or that a
real device is prepared, attached through CDI, healthy, or ready for a
workload.
