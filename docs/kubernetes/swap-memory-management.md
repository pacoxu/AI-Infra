---
status: Active
maintainer: pacoxu
last_updated: 2026-04-01
tags: kubernetes, kubelet, swap, memory-management, cgroupv2, eviction
canonical_path: docs/kubernetes/swap-memory-management.md
---

# Kubernetes Swap Memory Management

This page is a practical companion for operating swap-enabled Kubernetes Linux nodes.

Status in this page is aligned to upstream state as of **2026-04-01**.

## Current Upstream Status

- `KEP-2400` ([issue #2400](https://github.com/kubernetes/enhancements/issues/2400)) is complete.
  - stage: stable
  - KEP status: implemented
  - milestone: v1.34
- Follow-up items are still in progress:
  - [#5359 Workload Controlled Swap](https://github.com/kubernetes/enhancements/issues/5359)
  - [#5424 Swap-Aware Scheduling](https://github.com/kubernetes/enhancements/issues/5424)
  - [#5433 Swap-Aware Evictions](https://github.com/kubernetes/enhancements/issues/5433)

## Prerequisites

- Linux nodes
- cgroup v2 for workload swap support path
- swap already provisioned on host (file or partition)

## Kubelet Configuration

### Baseline (allow kubelet start, keep workloads non-swap)

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
failSwapOn: false
memorySwap:
  swapBehavior: NoSwap
```

### Enable workload swap

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
failSwapOn: false
memorySwap:
  swapBehavior: LimitedSwap
```

## Behavior Model

- `NoSwap` (default): Kubernetes-managed workloads do not use swap.
- `LimitedSwap`: workloads can use swap under kubelet/CRI rules.
- Swap allocation is automatic and request-proportional (under current model):

```text
containerSwapLimit = (containerMemoryRequest / nodeTotalMemory) * totalPodsSwapAvailable
```

- Current implementation is intentionally conservative and not yet full workload-level policy control.

## Observability

### Kubelet endpoints and metrics

- `/metrics/resource`
  - `node_swap_usage_bytes`
  - `container_swap_usage_bytes`
  - `container_swap_limit_bytes`
- `/stats/summary`

### Useful commands

```bash
kubectl top nodes --show-swap
kubectl top pods -A --show-swap
kubectl get nodes -o go-template='{{range .items}}{{.metadata.name}}: {{if .status.nodeInfo.swap.capacity}}{{.status.nodeInfo.swap.capacity}}{{else}}<unknown>{{end}}{{"\n"}}{{end}}'
```

### Discover nodes with swap via NFD label

```bash
kubectl get nodes -o jsonpath='{range .items[?(@.metadata.labels.feature\.node\.kubernetes\.io/memory-swap)]}{.metadata.name}{"\t"}{.metadata.labels.feature\.node\.kubernetes\.io/memory-swap}{"\n"}{end}'
```

## Memory Pressure Tuning Guidance

Use kernel reclaim and kubelet eviction together as one control loop.

Key knobs:

- `vm.swappiness`
- `vm.min_free_kbytes`
- `vm.watermark_scale_factor`
- kubelet eviction thresholds (`memory.available`)

Common starting point from SIG Node deep-dive materials (benchmark before production rollout):

- `vm.swappiness = 60`
- `vm.min_free_kbytes` around 2-3% of physical memory
- `vm.watermark_scale_factor` significantly above default to widen reclaim runway

Operational goals:

- start reclaim/swap early enough to avoid hard OOM spikes
- avoid reclaim so early that workloads thrash and latency collapses
- keep kubelet eviction and kernel reclaim thresholds aligned

## Risks and Guardrails

- Swap can degrade latency if active working set is swapped.
- Poor tuning can cause OOM before kubelet eviction completes.
- Scheduler is not fully swap-aware yet.
- Encrypt swap where possible.
- Prefer isolated and fast backing storage (SSD/NVMe).
- Protect system-critical daemons from swap and I/O starvation.

## Related Reading

- [Kubernetes swap memory management docs](https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/)
- [Linux node swap behaviors](https://kubernetes.io/docs/reference/node/swap-behavior/)
- [KEP-2400 issue](https://github.com/kubernetes/enhancements/issues/2400)
- [KEP-2400 design](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2400-node-swap)
- [Kubernetes 1.28 swap beta blog](https://kubernetes.io/blog/2023/08/24/swap-linux-beta/)
- [Kubernetes 1.32 swap improvements blog](https://kubernetes.io/blog/2025/03/25/swap-linux-improvements/)
- [Linux swap tuning deep dive](https://kubernetes.io/blog/2025/08/19/tuning-linux-swap-for-kubernetes-a-deep-dive/)
