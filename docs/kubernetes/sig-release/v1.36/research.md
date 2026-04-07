# Kubernetes v1.36 Release Blog Research (Issue #34)

- Issue: https://github.com/DaoCloud-OpenSource/docs/issues/34
- Scope of this delivery: step 1 only (collect and organize information, no EN/ZH blog draft yet)
- Snapshot time (UTC+8): 2026-03-18

## 1) Issue Context

Issue #34 currently contains only:

- Title: `Kubernetes v1.36  release blog`
- Body: `following previous blogs`

So this research pack is built as the input foundation for later writing.

## 2) Existing Local Templates and Style in This Repo

Relevant local references:

- `kubernetes/sig-release/how-to-write-release-blog.md`
- `kubernetes/sig-release/v1.35/release.md`
- `kubernetes/sig-release/v1.34/release.md`
- `kubernetes/sig-release/v1.33/release.md`

Observed structure pattern (recent versions):

1. headline + release date + theme
2. release logo/theme interpretation
3. install/upgrade notes
4. GA/stable highlights
5. beta highlights
6. alpha highlights
7. deprecations/removals
8. DaoCloud/community contributions
9. references + historical links

## 3) Official v1.36 Timeline (Upstream)

Source:

- https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/README.md

Key dates:

- Release cycle start: 2026-01-12
- Production Readiness Freeze: 2026-02-04 (AoE) / 2026-02-05 12:00 UTC
- Enhancements Freeze: 2026-02-11 (AoE) / 2026-02-12 12:00 UTC
- Feature blog freeze: 2026-02-26 (AoE) / 2026-02-27 12:00 UTC
- Code Freeze + Test Freeze: 2026-03-18 (AoE) / 2026-03-19 12:00 UTC
- Docs Freeze: 2026-04-08 (AoE) / 2026-04-09 12:00 UTC
- Planned GA release (`v1.36.0`): 2026-04-22

Current point-in-time (this research snapshot): code/test freeze day.

## 4) Official People and Tracking Boards

Release team and tracking links:

- Release team: https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-team.md
- Links index: https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/links.md
- Enhancements board: https://github.com/orgs/kubernetes/projects/241/views/1
- Bug triage board: https://github.com/orgs/kubernetes/projects/80/views/29
- CI signal board: https://github.com/orgs/kubernetes/projects/68/views/41
- Kubernetes milestone v1.36: https://github.com/kubernetes/kubernetes/milestone/69

Milestone snapshot (`kubernetes/kubernetes` milestone #69):

- open issues: 20
- closed issues: 955
- state: open
- updated_at: 2026-03-18T08:56:41Z

## 5) Changelog and Release Notes Draft Status

Primary sources:

- Changelog: https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md
- Release notes draft: https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/release-notes/release-notes-draft.md

Current changelog state:

- includes `v1.36.0-alpha.1`
- includes `v1.36.0-alpha.2`
- no final `v1.36.0` section yet (expected at/near GA)

Release notes draft includes major sections already:

- Urgent Upgrade Notes
- Changes by Kind (Dependency / Deprecation / API Change / Feature / Failing Test / Bug or Regression / Other)

High-signal upgrade/risk notes already present:

- Scheduler plugin interface changes (PreBind parallel opt-in, PostFilterResult change)
- kubeadm removes integrated flex-volume support
- `git-repo` volume plugin disabled by default and cannot be re-enabled
- multiple API/client-go behavior and feature-gate lock changes

## 6) Release Highlights Discussion (Direct Input for Blog Angle)

Discussion thread:

- https://github.com/kubernetes/sig-release/discussions/2958

Thread metadata:

- created: 2026-02-11
- highlights submission deadline in body: 2026-03-31

Current comments found in thread snapshot:

1. SIG Network highlight:
- KEP-4858 IP/CIDR validation improvements to Beta
- focus: canonical formats, security/interoperability

2. SIG Storage highlight set:
- KEP-3476 VolumeGroupSnapshot (target GA)
- KEP-5538 ServiceAccount token via secrets for CSI (target GA)
- KEP-4876 Mutable volume attach limits (target GA)
- KEP-1710 SELinux relabeling improvements (target GA)
- driver disable callout: `gitRepo` plugin disabled in 1.36

Raw snapshots are saved in:

- `data/sig-release-discussion-2958.json`
- `data/sig-release-discussion-2958-comments.json`

## 7) Enhancements Inventory Snapshot (Milestone v1.36)

Raw data file:

- `data/enhancements-v1.36-tracked.json`

Collection method:

- open issues in `kubernetes/enhancements` with `tracked/yes`
- filtered to milestone title `v1.36`

Counts:

- tracked+milestone=v1.36: 78
- stage/alpha: 31
- stage/beta: 25
- stage/stable: 18
- stage/unknown: 4

Top SIG distribution (count among these 78):

- sig/node: 35
- sig/scheduling: 17
- sig/api-machinery: 11
- sig/auth: 11
- sig/storage: 9

`stage/unknown` items (worth manual check later):

- #5732 Topology-aware workload scheduling
- #5710 Workload-aware preemption
- #5681 Conditional Authorization
- #5679 HPA External Metrics Fallback on Retrieval Failure

Tracked items with `milestone == null` seen in source pull (important for watchlist):

- #5707 Deprecate `service.spec.externalIPs`
- #4858 IP/CIDR validation improvements

## 8) Candidate Topics to Prioritize in Future Blog Draft (Not Drafted Yet)

From stable-targeted tracked enhancements and current notes, high-probability candidates include:

- KEP-3962 Mutating Admission Policies (GA)
- KEP-5589 Remove gogo protobuf dependency
- KEP-5538 CSI driver SA token via secrets
- KEP-4876 Mutable CSINode allocatable
- KEP-3476 VolumeGroupSnapshot
- KEP-2258 Node log query
- KEP-1710 SELinux relabel speedup
- KEP-127 User Namespaces in pods

From beta-targeted tracked enhancements (probable mention set):

- KEP-4006 Transition from SPDY to WebSockets
- KEP-5311 Relaxed validation for Service names
- KEP-5284 Constrained Impersonation
- KEP-4680 Resource Health Status (device plugin/DRA)
- KEP-4827/4828 Statusz and Flagz
- KEP-5040 Remove gitRepo volume driver

## 9) Related Upstream Website Signals

Notable open PRs in `kubernetes/website`:

- Mid-cycle/sneak peek WIP: https://github.com/kubernetes/website/pull/54866
  - file path in PR: `content/en/blog/_posts/2026/kubernetes-v1-36-sneak-peak.md`
- additional v1.36 related docs/blog placeholders are also open (multiple PRs)

This indicates upstream messaging is still in-flight, so final wording should be re-checked near GA.

## 10) Known-Issue Tracking Status (Current Snapshot)

Searches in `kubernetes/kubernetes` did not return v1.36-specific `known issue` results yet.

Interpretation for now:

- no explicit v1.36 known-issue ticket surfaced by the queries used in this snapshot
- still needs final check near GA day before publishing

## 11) Release Exception Context (Potential Risk/Story Input)

Source:

- https://github.com/kubernetes/sig-release/blob/master/releases/release-1.36/exceptions.yaml

Enhancements freeze exceptions recorded there include approved and rejected requests.
This can be used later for "what slipped/what got in" context if needed.

## 12) Gaps To Re-Check Right Before Writing (Step 2/3)

1. final release blog URL and final theme/logo assets
2. final CHANGELOG `v1.36.0` section (replace alpha-only assumptions)
3. final release notes draft vs final notes differences
4. v1.36 known issues (if any appear close to release)
5. whether milestone issue counts and tracked enhancements changed materially

---

This file is intentionally research-only and can be treated as source material for:

- step 2: English blog drafting
- step 3: Chinese blog drafting

