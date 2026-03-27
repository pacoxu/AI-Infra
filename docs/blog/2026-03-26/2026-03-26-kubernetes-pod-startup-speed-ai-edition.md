---
status: Active
maintainer: pacoxu
date: 2026-03-26
tags: kubernetes, pod, startup, optimization, ai, gpu, cold-start, inference
canonical_path: docs/blog/2026-03-26/2026-03-26-kubernetes-pod-startup-speed-ai-edition.md
source_urls:
  - https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
  - https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/
  - https://kubernetes.io/docs/tasks/administer-cluster/node-overprovisioning/
  - https://kserve.github.io/website/
  - https://github.com/containerd/stargz-snapshotter
  - https://github.com/containerd/nydus-snapshotter
  - https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke
---

# Kubernetes Pod Startup Speed Optimization Guide: AI Edition

[中文版本](./2026-03-26-kubernetes-pod-startup-speed-ai-edition_zh.md)

For AI inference and training platforms, the goal is not just “container
started,” but **business-ready serving**. Teams often spend cycles on isolated
tuning and miss the real bottleneck: the end-to-end cold-start critical path.

This guide focuses on one principle: **measure startup by stages, then remove
or reuse the expensive stages**.

## TL;DR

Use this decomposition:

`T_total = T_capacity + T_schedule + T_image + T_model + T_runtime + T_warmup`

- `T_capacity`: node scale-up, GPU stack readiness, device plugin reporting
- `T_schedule`: scheduler placement
- `T_image`: image pull, unpack, mount
- `T_model`: model artifacts available locally
- `T_runtime`: GPU/framework first-time init
- `T_warmup`: first compile and warmup inference

In practice, `T_capacity + T_model + T_warmup` usually dominate.

## Why AI Pods Are Harder

1. `Ready` may still be cold: model not loaded, kernels not compiled.
2. Artifact surfaces are much larger: image + weights + tokenizer + caches.
3. Hardware constraints are stronger: GPU, NUMA, MIG, sharing policies.

That is why “Pod startup tuning” for AI must span control plane, node runtime,
and serving path.

## Define “Startup Complete” First

Standardize milestones before optimization:

| Stage | Signal |
| --- | --- |
| Scheduling done | `PodScheduled=True` |
| Sandbox/network ready | `PodReadyToStartContainers=True` (if available) |
| Init done | `Initialized=True` |
| Containers ready | `ContainersReady=True` |
| Business ready | `Ready=True` + custom AI gates |

Use `readinessGates` so traffic only hits fully warmed instances:

```yaml
spec:
  readinessGates:
    - conditionType: ai.example.com/ModelLoaded
    - conditionType: ai.example.com/WarmupDone
```

## Segmented Observability

Minimum baseline:

1. Emit all six stage durations for every Pod.
2. Break `Pending` into “waiting for capacity vs scheduling vs image.”
3. Track P50/P95/P99 for `ModelLoaded` and `WarmupDone`.
4. Build startup budgets by model class (for example 7B/13B/70B).

If you only track “create -> Ready,” you cannot do reliable root-cause analysis.

## Optimization Order (Highest ROI First)

### 1) Fix capacity readiness first (`T_capacity`)

- Keep minimum reserved capacity for critical online workloads.
- Monitor “Node Ready -> GPU schedulable” delay.
- Pre-initialize driver/runtime/device plugin during node preparation.

Many AI platforms are slow here: node is online, but GPU resources are not yet
advertised to the scheduler.

### 2) Move artifact distribution off the path (`T_image + T_model`)

- Image layer: optimize image size, enable parallel pulls, consider lazy pull.
- Model layer: use cacheable OCI-style model artifacts plus node-local cache.
- Avoid full remote model download per Pod.

Example kubelet settings (validate against node disk/network limits):

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
serializeImagePulls: false
maxParallelImagePulls: 5
```

### 3) Reuse one-time initialization (`T_runtime + T_warmup`)

- Persist CUDA/JIT/framework compile caches.
- Keep `torch.compile` cache on persistent or node-local fast storage.
- Enable engine/runtime cache in your serving stack.

Example environment variables:

```bash
CUDA_CACHE_PATH=/var/cache/cuda
TORCHINDUCTOR_CACHE_DIR=/var/cache/torchinductor
HF_HOME=/var/cache/huggingface
```

### 4) Bind warmup to readiness

- `startupProbe` protects long init windows.
- `readinessProbe` / `readinessGates` block traffic until warmup is done.
- In canaries, gate rollout on first-request latency, not only error rate.

### 5) Optimize scheduling complexity last (`T_schedule`)

- Reduce over-constrained affinity/anti-affinity rules.
- Surface topology constraints for multi-GPU/NUMA workloads.
- For fine-grained device selection, use DRA/ResourceClaim instead of label
  explosion.

Scheduling matters, but it is rarely the first lever in AI cold start.

## Common Anti-Patterns

1. Treating `Ready` as business-ready.
2. Downloading model artifacts during app startup without caching.
3. Keeping all caches in `emptyDir` so every restart is cold again.
4. Tuning HPA only while ignoring node autoscaler and node warmup latency.
5. Using a single oversized image for every model/runtime combination.

## A Practical 30-Day Rollout

1. Week 1: instrument segmented metrics and define startup budgets.
2. Week 2: optimize image/model distribution and validate `T_image+T_model`.
3. Week 3: land cache reuse + warmup gating to reduce `T_runtime+T_warmup`.
4. Week 4: clean scheduling rules and capacity policy, stabilize P95/P99.

## Final Takeaway

AI Pod startup optimization is critical-path engineering:

- move capacity wait out of the request path,
- move large artifact transfer out of the request path,
- convert one-time initialization into reusable cache assets,
- and define `Ready` as true business readiness.

Do these consistently, and cold starts become predictable instead of random.

---

## Related Reading

- [Pod Startup Speed](../../kubernetes/pod-startup-speed.md)
- [GPU Pod Cold Start Optimization](../../kubernetes/gpu-pod-cold-start.md)
- [Kubernetes Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Dynamic Resource Allocation (DRA)](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [Node Overprovisioning](https://kubernetes.io/docs/tasks/administer-cluster/node-overprovisioning/)
- [Stargz Snapshotter](https://github.com/containerd/stargz-snapshotter)
- [Nydus Snapshotter](https://github.com/containerd/nydus-snapshotter)
- [KServe Documentation](https://kserve.github.io/website/)
- [GKE Agent Sandbox](https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke)
