# Kubernetes v1.36 English Draft (Writing-Day Recheck: 2026-03-19)

This draft is refreshed with upstream status rechecked on **March 19, 2026 (UTC+8)**.

## Writing-Day Upstream Status Recheck

### 1) Final release date confirmation

Current official release-cycle source still shows:

- planned v1.36 GA release date: **Wednesday, April 22, 2026**
- source: `kubernetes/sig-release` release-1.36 README
- upstream file revision checked: `sha e674160cb986b4244d1fdcafe6d499ee536626bf`

Reference: <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/README.md>

### 2) Final release blog / theme / logo links

As of this recheck:

- no final v1.36 release blog post is published in `kubernetes/website` blog post folder for 2026
- no final v1.36 logo assets are published in `kubernetes/sig-release/releases/release-1.36/logo` (only `.gitkeep`)
- there is still an open WIP mid-cycle/release PR: <https://github.com/kubernetes/website/pull/54866>

Therefore, final official blog/theme/logo links are **not available yet**.

### 3) Final CHANGELOG-1.36.md and release-notes changes

### CHANGELOG-1.36.md (upstream status)

Current changelog still contains pre-GA entries:

- `v1.36.0-alpha.1`
- `v1.36.0-alpha.2`
- no final `v1.36.0` GA section yet
- upstream file revision checked: `sha 37cd7afb115a346467ab778cd9a3104140c65c7a`

Reference: <https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md>

### release-notes-draft.md (upstream status)

Current draft still has expected pre-GA structure:

- `Urgent Upgrade Notes`
- `Deprecation`
- `API Change`
- `Feature`
- `Bug or Regression`
- upstream file revision checked: `sha d8abece0a18ba0c65eda46bea130b499cc9fe3b1`

Reference: <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-notes/release-notes-draft.md>

## Executive Summary

Kubernetes v1.36 is in late-cycle pre-GA state. The strongest current signal is not a finalized marketing narrative yet, but the technical direction:

1. policy and API machinery maturity continues (notably `MutatingAdmissionPolicy` and protobuf cleanup)
2. storage/DRA capabilities keep moving toward production use
3. node/scheduler changes require plugin and controller compatibility validation before upgrade
4. deprecation/removal items (`gitRepo` plugin, flex-volume integration path in kubeadm) need explicit operator attention

## Major Highlights By Stage

### GA / Stable Highlights (verified)

- [KEP-3962 Mutating Admission Policies](https://github.com/kubernetes/enhancements/issues/3962)
- [KEP-5589 Remove gogo protobuf dependency for Kubernetes API types](https://github.com/kubernetes/enhancements/issues/5589)
- [KEP-3476 VolumeGroupSnapshot](https://github.com/kubernetes/enhancements/issues/3476)
- [KEP-4876 Mutable CSINode Allocatable Property](https://github.com/kubernetes/enhancements/issues/4876)
- [KEP-5538 CSI driver SA token via secrets field](https://github.com/kubernetes/enhancements/issues/5538)
- [KEP-2258 Node log query](https://github.com/kubernetes/enhancements/issues/2258)
- [KEP-127 User Namespaces in pods](https://github.com/kubernetes/enhancements/issues/127)

### Beta Highlights (verified)

- [KEP-4006 Transition from SPDY to WebSockets](https://github.com/kubernetes/enhancements/issues/4006)
- [KEP-5311 Relaxed validation for Services names](https://github.com/kubernetes/enhancements/issues/5311)
- [KEP-5284 Constrained Impersonation](https://github.com/kubernetes/enhancements/issues/5284)
- [KEP-4680 Resource Health Status](https://github.com/kubernetes/enhancements/issues/4680)
- [KEP-4858 IP/CIDR validation improvements](https://github.com/kubernetes/enhancements/issues/4858): currently `stage/beta`, but does **not** currently show milestone `v1.36` on its issue metadata

### Alpha Highlights (verified)

- [KEP-5866 Server-side Sharded List and Watch](https://github.com/kubernetes/enhancements/issues/5866)
- [KEP-5882 Deployment Pod Replacement Policy](https://github.com/kubernetes/enhancements/issues/5882)
- [KEP-5729 DRA: ResourceClaim Support for Workloads](https://github.com/kubernetes/enhancements/issues/5729)

## Highlights Reported In `kubernetes/sig-release#2958`

`kubernetes/sig-release` discussion [#2958](https://github.com/kubernetes/sig-release/discussions/2958) contains cross-SIG release highlights. The features below were explicitly called out there and rechecked against current enhancement metadata on **March 23, 2026 (UTC+8)**.

### KEP-4858: IP/CIDR Validation Improvements (Beta)

This change tightens validation so non-canonical IP/CIDR forms are rejected more consistently, reducing ambiguity between API input, controller logic, and network policy behavior. For operators, the main impact is configuration hygiene: legacy or loosely formatted addresses that previously slipped through can become upgrade blockers once stricter validation gates are enforced.

### KEP-3476: VolumeGroupSnapshot (GA target in v1.36)

Volume group snapshots extend snapshot semantics from single PVCs to related volume sets, which matters for applications that must preserve write-order consistency across multiple disks. This is particularly useful for coordinated backup/recovery workflows where training checkpoints, metadata, and model state must be captured as one logical unit.

### KEP-5538: Service Account Tokens For CSI Via `secrets` Field (GA target in v1.36)

This feature standardizes how CSI drivers receive scoped service account tokens through the `secrets` field path, reducing ad hoc credential wiring and helping operators align with short-lived token best practices. In production, it simplifies credential rotation and strengthens least-privilege boundaries between storage plugins and workloads.

### KEP-4876: Mutable `CSINode` Allocatable (GA target in v1.36)

Allowing mutable allocatable values in `CSINode` lets storage capacity signals track runtime reality instead of static startup assumptions. The practical outcome is better scheduling decisions for attach-limited environments and fewer false placements caused by stale volume-attachment limits.

### KEP-1710: SELinux Relabeling With Mount Options For Non-RWOP Volumes (GA target in v1.36)

This work improves SELinux labeling behavior for non-RWOP volume scenarios by using mount-option-based handling, lowering relabel overhead and reducing contention for shared-volume use cases. Clusters with strict SELinux enforcement can get more predictable startup behavior while keeping confinement guarantees intact.

### KEP-5040: `gitRepo` Volume Plugin Disabled In v1.36

`gitRepo` has long-standing security and maintenance concerns, and v1.36 continues the removal path by disabling it. Teams that still rely on `gitRepo` must migrate to safer patterns such as init containers, CSI-backed content distribution, or build-time artifact packaging before production rollout.

### KEP-3104: `kubectl` User Preferences (`kuberc`) (Beta target in v1.36)

The `kuberc` effort separates user preferences from cluster connection data and expands CLI behavior customization, including credential-plugin-related workflows. This improves UX consistency for platform teams that manage many contexts and helps make local `kubectl` behavior more explicit and reviewable.

### KEP-5547: Workload APIs For Job Controller (Alpha target in v1.36)

This alpha introduces workload-oriented API direction around Job execution, aiming to better express workload intent and improve controller integration patterns. For early adopters, it is primarily an experimentation track to validate API shape and controller semantics rather than an immediate production default.

### KEP-5440: Mutable Container Resources In Suspended Jobs (Beta target in v1.36)

Promoting this capability to beta allows resource requests/limits adjustments while Jobs are suspended, enabling safer queue-time tuning before execution begins. It is useful in batch/AI pipelines where capacity planning often changes between submission and actual start time.

### Scalability Signal: Tested Resource Size Raised From 800MB To 1.5GB

SIG Scalability also called out the increase in tested resource size envelope (from 800MB to 1.5GB) under ongoing scalability work. While not itself a user-facing API feature, it signals stronger confidence in control-plane handling of larger object payload scenarios and helps frame risk for large-cluster operators.

### Additional Reply Highlights (March 24, 2026 update)

Discussion replies added additional highlights beyond the original top-level comments:

#### KEP-5707: Deprecate `Service.spec.externalIPs` (deprecation process starts in v1.36)

SIG Network called out that v1.36 starts the deprecation path for `Service.spec.externalIPs` by introducing warnings on usage. This is an early but important operator signal: teams should begin inventory and migration planning now to avoid being forced into late-cycle changes once stronger restrictions arrive in later releases.

#### KEP-3157: Watch List / Streaming Initial List (highlighted by SIG API Machinery)

This capability allows informer initialization to obtain initial state through a streaming watch path rather than LIST chunking, which reduces API server memory pressure and improves large-cluster bootstrap behavior. For platform teams, the main value is lower read amplification during controller startup and relist-heavy periods.

#### KEP-4988: Snapshottable API Server Cache (highlighted by SIG API Machinery)

This work enables point-in-time snapshots from the watch cache so paginated LIST requests can be served from cache more often instead of falling back to etcd. Combined with recent cache-read improvements, it supports a multi-release API read-path optimization direction for better scalability and latency stability.

#### KEP-5073: Declarative Validation of Native Types (highlighted by SIG API Machinery)

This feature applies CEL-based declarative validation to built-in Kubernetes types through `validation-gen`, reducing the maintenance burden of handwritten validation logic in Go. The practical impact is improved consistency and reviewability of validation rules across native APIs.

#### KEP-5793: Manifest-Based Admission Control Config (Alpha in v1.36)

This alpha introduces startup-time manifest configuration for admission webhooks/policies in kube-apiserver, ensuring selected policies are active before request handling begins. It is especially relevant for platform security baselines where bootstrap enforcement guarantees matter.

## Upgrade / Deprecation Risk Notes

From current changelog and release-notes draft signals, prioritize these upgrade checks:

1. Scheduler plugin compatibility: interface/behavior updates around `PreBind` and `PostFilter`-related mechanics require retesting for custom scheduler plugins.
2. kubeadm + flex-volume path changes: integrated flex-volume support behavior in kubeadm has changed; clusters still relying on legacy paths need migration/custom handling.
3. `gitRepo` volume plugin direction: current release-note direction indicates disabled-by-default behavior without re-enable path.
4. API/client-go behavior shifts: informer and API machinery correctness/performance changes may surface hidden assumptions in custom controllers/operators.

## AI-Infra Action List

For AI platform / AI-Infra teams (GPU and mixed training/inference workloads), use this execution checklist:

1. Runtime baseline audit: verify `containerd`, `runc/crun`, and cgroup mode by node pool.
2. Scheduler canary validation: test custom scheduling behavior against v1.36 changes with representative AI workloads.
3. DRA readiness review: confirm CRDs/controllers/device plugins are aligned with current DRA direction.
4. Storage recovery drill: validate snapshot/restore workflows for model-serving and training-state volumes.
5. Admission policy migration review: identify mutating webhook rules that can migrate to `MutatingAdmissionPolicy`.
6. Controller regression sweep: run tests for client-go informer and API behavior assumptions.
7. Network data hygiene: clean non-canonical IP/CIDR entries before stricter validation bites.
8. Progressive rollout gates: enforce staged rollout with explicit rollback and AI SLO checks.

## Final Validation Before Publish

### KEP stage and target release still unchanged?

Rechecked on writing day for referenced KEPs:

- `3962`: `stage/stable`, milestone `v1.36`
- `5589`: `stage/stable`, milestone `v1.36`
- `3476`: `stage/stable`, milestone `v1.36`
- `4876`: `stage/stable`, milestone `v1.36`
- `5538`: `stage/stable`, milestone `v1.36`
- `2258`: `stage/stable`, milestone `v1.36`
- `127`: `stage/stable`, milestone `v1.36`
- `4858`: `stage/beta`, milestone `null`
- `4006`: `stage/beta`, milestone `v1.36`
- `5311`: `stage/beta`, milestone `v1.36`
- `5284`: `stage/beta`, milestone `v1.36`
- `4680`: `stage/beta`, milestone `v1.36`
- `5866`: `stage/alpha`, milestone `v1.36`
- `5882`: `stage/alpha`, milestone `v1.36`
- `5729`: `stage/alpha`, milestone `v1.36`
- `1710`: `stage/stable`, milestone `v1.36`
- `5040`: `stage/beta`, milestone `v1.36`
- `3104`: `stage/beta`, milestone `v1.36`
- `5547`: `stage/alpha`, milestone `v1.36`
- `5440`: `stage/beta`, milestone `v1.36`
- `5707`: `stage/none`, milestone `null`
- `3157`: `stage/beta`, milestone `null`
- `4988`: `stage/beta`, milestone `null`
- `5073`: `stage/beta`, milestone `v1.36`
- `5793`: `stage/alpha`, milestone `v1.36`

Note: the March 24, 2026 reply in discussion `#2958` frames `3157`, `4988`, and `5073` as stable-graduation highlights, but current enhancement issue labels still show `stage/beta` for these three items.

### Any newly disclosed known issue?

Writing-day queries found **no** v1.36 known-issue ticket in `kubernetes/kubernetes` for:

- title search: `"known issue"` + `1.36`
- label/milestone search: `label:kind/known-issue milestone:v1.36`

This should still be rechecked again right before final publication.

## References

- <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/README.md>
- <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-team.md>
- <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/links.md>
- <https://github.com/kubernetes/kubernetes/milestone/69>
- <https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md>
- <https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-notes/release-notes-draft.md>
- <https://github.com/kubernetes/sig-release/discussions/2958>
- <https://github.com/kubernetes/website/pull/54866>
