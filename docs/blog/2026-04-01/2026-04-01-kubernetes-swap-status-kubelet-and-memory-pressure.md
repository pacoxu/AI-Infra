---
status: Active
maintainer: pacoxu
date: 2026-04-01
tags: kubernetes, kubelet, swap, memory-pressure, sig-node, eviction, scheduling
canonical_path: docs/blog/2026-04-01/2026-04-01-kubernetes-swap-status-kubelet-and-memory-pressure.md
source_urls:
  - https://github.com/kubernetes/enhancements/issues/2400
  - https://github.com/kubernetes/enhancements/issues/5359
  - https://github.com/kubernetes/enhancements/issues/5424
  - https://github.com/kubernetes/enhancements/issues/5433
  - https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2400-node-swap
  - https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/
  - https://kubernetes.io/docs/reference/node/swap-behavior/
  - https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/
  - https://kubernetes.io/blog/2023/08/24/swap-linux-beta/
  - https://kubernetes.io/blog/2025/03/25/swap-linux-improvements/
  - https://kubernetes.io/blog/2025/08/19/tuning-linux-swap-for-kubernetes-a-deep-dive/
  - https://www.youtube.com/watch?v=bFrEPfls5PQ
  - https://www.youtube.com/watch?v=El94Z0JowF0
---

# Kubernetes Swap Status in 2026: kubelet behavior, memory pressure, and what is next

This post summarizes the current status of swap in Kubernetes and kubelet, mainly around KEP-2400 and related follow-up enhancements.

All status statements below are checked as of **2026-04-01**.

## TL;DR

- `KEP-2400` (Node memory swap support) is **done and closed**.
  - Enhancement issue: `#2400` closed on **2025-09-17**.
  - KEP status is `implemented`, `stage: stable`, latest milestone `v1.34`.
- `NodeSwap` is already listed as **GA in Kubernetes 1.34**.
- Current kubelet model is intentionally conservative:
  - `NoSwap` is default behavior.
  - `LimitedSwap` is opt-in.
  - swap for workloads is Linux + cgroup v2 only.
- The next big step is not “turn swap on”, but “make scheduling/eviction/workload APIs swap-aware”.
  - `#5359` workload-controlled swap
  - `#5424` swap-aware scheduling
  - `#5433` swap-aware evictions

## 1) Current status snapshot

### KEP-2400

- Issue: [kubernetes/enhancements#2400](https://github.com/kubernetes/enhancements/issues/2400)
- Title: `Node memory swap support`
- State: `CLOSED`
- Closed at: **2025-09-17**
- Labels include: `sig/node`, `stage/stable`
- Milestone: `v1.34`

### Follow-up enhancement issues (WIP)

- [#5359 Workload Controlled Swap](https://github.com/kubernetes/enhancements/issues/5359)
  - State: `OPEN`
  - Labels include `stage/alpha`, `tracked/no`
  - Updated: **2026-02-12**
- [#5424 Swap-Aware Scheduling](https://github.com/kubernetes/enhancements/issues/5424)
  - State: `OPEN`
  - Currently placeholder-level content
  - Updated: **2026-03-16**
- [#5433 Swap-Aware Evictions](https://github.com/kubernetes/enhancements/issues/5433)
  - State: `OPEN`
  - Currently placeholder-level content
  - Updated: **2026-01-20**

## 2) Timeline: how we got here

- **v1.22 (Alpha)**: initial NodeSwap support path starts.
- **v1.28 (Beta1)**:
  - Linux swap support promoted to beta.
  - cgroup v2 support hardened.
  - swap metrics exposed via `/metrics/resource` and `/stats/summary`.
  - At that time, `UnlimitedSwap` / `LimitedSwap` behavior still appeared in docs/blog context.
- **v1.30-v1.33 (Beta2/Beta3)**:
  - behavior tightened toward safer defaults.
  - `NoSwap` becomes default direction for workloads.
  - high-priority workloads restricted from swap.
  - memory-backed volume `noswap` handling improved.
- **v1.34 (Stable/GA)**:
  - KEP-2400 reaches stable and is marked implemented.
  - Feature gates reference lists `NodeSwap` as GA starting 1.34.

## 3) kubelet behavior now (practical model)

For Linux nodes, kubelet swap behavior is controlled mainly by:

1. `failSwapOn`
2. `memorySwap.swapBehavior`

Example:

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
failSwapOn: false
memorySwap:
  swapBehavior: NoSwap
```

Available behaviors now:

- `NoSwap` (default): Kubernetes-managed workloads do not use swap.
- `LimitedSwap`: workloads can use swap with Kubernetes rules.

Important constraints in current design:

- Workload swap support is for **Linux + cgroup v2** path.
- Under `LimitedSwap`, swap amount is auto-calculated from memory request proportion:

```text
containerSwapLimit = (containerMemoryRequest / nodeTotalMemory) * totalPodsSwapAvailable
```

- This is why KEP-2400 is a node-level baseline capability, not the final per-workload policy framework.

## 4) Observability and ops signals you should watch

Kubelet/metrics now make swap visible enough for production debugging:

- `/metrics/resource`
  - `node_swap_usage_bytes`
  - `container_swap_usage_bytes`
  - `container_swap_limit_bytes`
- `/stats/summary`
- `kubectl top --show-swap`
- node status swap capacity (`node.status.nodeInfo.swap.capacity`)

Useful commands:

```bash
kubectl top nodes --show-swap
kubectl top pods -A --show-swap
kubectl get nodes -o go-template='{{range .items}}{{.metadata.name}}: {{if .status.nodeInfo.swap.capacity}}{{.status.nodeInfo.swap.capacity}}{{else}}<unknown>{{end}}{{"\n"}}{{end}}'
```

## 5) Memory pressure handling: kernel vs kubelet

The strongest practical lesson from the 2025 deep-dive and talks is:

- Kubernetes eviction and Linux reclaim/swap are related but different loops.
- If tuning is poor, OOM killer may happen before kubelet eviction finishes.

Key Linux tuning knobs repeatedly highlighted:

- `vm.swappiness`
- `vm.min_free_kbytes`
- `vm.watermark_scale_factor`

A commonly cited starting point (must be workload-tested):

- `vm.swappiness = 60`
- `vm.min_free_kbytes` around 2-3% of node memory
- `vm.watermark_scale_factor` significantly above default (for a wider reclaim runway)

And the Kubernetes-side reminder from docs:

- tune eviction thresholds with awareness of kernel reclaim thresholds (`min_free_kbytes`) so swapping has room to work before hard failure.

## 6) What is still missing in upstream behavior

KEP-2400 intentionally did **not** solve everything:

- scheduler still does not fully account for swap as a scheduling resource
- eviction logic is not fully swap-aware by default policy
- pod/workload-level swap policies are still evolving

That gap is exactly why the follow-up issues exist:

- [#5359](https://github.com/kubernetes/enhancements/issues/5359): workload/pod-level swap controls
- [#5424](https://github.com/kubernetes/enhancements/issues/5424): scheduling awareness
- [#5433](https://github.com/kubernetes/enhancements/issues/5433): eviction awareness

## 7) Notes from the two conference slide decks

Two practical themes from the conference materials are useful when planning
production rollout:

- **KubeCon NA 2025 deep dive**:
  - reinforces the 1.22 -> 1.34 journey and the same three future tracks
    (workload control, eviction awareness, scheduling awareness)
  - emphasizes the OOM-vs-eviction race and “early reclaim runway” tuning via
    `vm.min_free_kbytes` and `vm.watermark_scale_factor`
- **KubeCon EU 2024 talk (Intel)**:
  - frames swap design as six control questions: what/how much/where/when/how
    to isolate effects/where control logic should live
  - highlights out-of-tree approaches (NRI plugins + memtierd) for process- or
    container-granularity policies that are not yet native in core Kubernetes

## 8) Recommended adoption path (2026)

1. Start with `NoSwap` + `failSwapOn: false` to validate node/system behavior first.
2. Move selective node pools to `LimitedSwap` (not whole fleet at once).
3. Keep control-plane nodes conservative (often no swap).
4. Prefer fast, isolated swap backing storage; encrypt swap.
5. Protect system daemons from swap / I/O starvation.
6. Enable swap dashboards and alerts before larger rollout.
7. Tune kernel reclaim + kubelet eviction together, not separately.

## References

- Main enhancement issue: [KEP-2400 issue](https://github.com/kubernetes/enhancements/issues/2400)
- KEP text: [keps/sig-node/2400-node-swap](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2400-node-swap)
- Official docs: [Swap memory management](https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/)
- Official docs: [Linux Node Swap Behaviors](https://kubernetes.io/docs/reference/node/swap-behavior/)
- Feature gates reference: [NodeSwap GA timeline](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)
- Blog: [Kubernetes 1.28 Beta support for using swap on Linux](https://kubernetes.io/blog/2023/08/24/swap-linux-beta/)
- Blog: [Fresh Swap Features for Linux Users in Kubernetes 1.32](https://kubernetes.io/blog/2025/03/25/swap-linux-improvements/)
- Blog: [Tuning Linux Swap for Kubernetes: A Deep Dive](https://kubernetes.io/blog/2025/08/19/tuning-linux-swap-for-kubernetes-a-deep-dive/)
- Talk: [Deep Dive: Handling Kubernetes Memory Pressure & Achieving Workload Stability With Swap](https://www.youtube.com/watch?v=bFrEPfls5PQ)
- Talk: [Swap Smart, Save Big](https://www.youtube.com/watch?v=El94Z0JowF0)
