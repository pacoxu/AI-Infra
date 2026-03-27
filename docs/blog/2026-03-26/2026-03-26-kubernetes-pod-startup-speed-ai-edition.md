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

## Implementation Blueprint (MVP)

The following skeleton turns high-level guidance into concrete implementation.

### 1) Enforce business readiness with `readinessGates` + `pods/status` patch

Declaring `readinessGates` is only half of the implementation. Your workload
or sidecar also needs to patch Pod status conditions.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pod-status-patcher
  namespace: ai
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-status-patcher
  namespace: ai
rules:
  - apiGroups: [""]
    resources: ["pods/status"]
    verbs: ["get", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-status-patcher
  namespace: ai
subjects:
  - kind: ServiceAccount
    name: pod-status-patcher
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-status-patcher
```

Inject Pod identity with Downward API:

```yaml
env:
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
  - name: POD_NAMESPACE
    valueFrom:
      fieldRef:
        fieldPath: metadata.namespace
```

Patch `ModelLoaded` and `WarmupDone` when initialization is complete:

```bash
#!/usr/bin/env sh
set -euo pipefail

NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
TOKEN="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
CA_CERT="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
API="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT_HTTPS}"

cat >/tmp/pod-status-patch.json <<EOF
{
  "status": {
    "conditions": [
      {
        "type": "ai.example.com/ModelLoaded",
        "status": "True",
        "reason": "WeightsReady",
        "lastTransitionTime": "${NOW}"
      },
      {
        "type": "ai.example.com/WarmupDone",
        "status": "True",
        "reason": "WarmupPassed",
        "lastTransitionTime": "${NOW}"
      }
    ]
  }
}
EOF

curl --fail --silent --show-error \
  --cacert "${CA_CERT}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/merge-patch+json" \
  -X PATCH \
  "${API}/api/v1/namespaces/${POD_NAMESPACE}/pods/${POD_NAME}/status" \
  --data-binary @/tmp/pod-status-patch.json
```

### 2) Move model download out of app startup with `initContainer` + node cache

Use OCI model artifacts and prefetch them in `initContainers`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-serving
  namespace: ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-serving
  template:
    metadata:
      labels:
        app: llm-serving
    spec:
      serviceAccountName: pod-status-patcher
      initContainers:
        - name: model-prefetch
          image: ghcr.io/oras-project/oras:v1.2.2
          command: ["/bin/sh", "-c"]
          args:
            - |
              set -euo pipefail
              if [ ! -f /model-cache/${MODEL_ID}/READY ]; then
                mkdir -p /model-cache/${MODEL_ID}
                oras pull "${MODEL_OCI_REF}" -o /model-cache/${MODEL_ID}
                touch /model-cache/${MODEL_ID}/READY
              fi
          env:
            - name: MODEL_ID
              value: llama-3-8b-fp16
            - name: MODEL_OCI_REF
              value: registry.example.com/models/llama-3-8b:fp16
          volumeMounts:
            - name: model-cache
              mountPath: /model-cache
      containers:
        - name: server
          image: registry.example.com/inference/vllm-openai:stable
          args: ["--model", "/models/llama-3-8b-fp16"]
          volumeMounts:
            - name: model-cache
              mountPath: /models
              readOnly: true
      volumes:
        - name: model-cache
          hostPath:
            path: /var/lib/ai-model-cache
            type: DirectoryOrCreate
```

For stricter multi-tenant environments, replace `hostPath` with Local PV or a
dedicated cache service plus quotas.

### 3) Reserve baseline capacity with placeholder Pods

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: overprovisioning
value: -10
globalDefault: false
description: "Low-priority placeholder pods for faster scale-out"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: overprovisioning
  namespace: kube-system
spec:
  replicas: 20
  selector:
    matchLabels:
      app: overprovisioning
  template:
    metadata:
      labels:
        app: overprovisioning
    spec:
      priorityClassName: overprovisioning
      terminationGracePeriodSeconds: 0
      containers:
        - name: pause
          image: registry.k8s.io/pause:3.9
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
```

When real workloads arrive, these low-priority Pods are preempted and capacity
is reclaimed quickly.

### 4) Instrument stage timestamps for postmortem-ready diagnostics

Start with a direct timestamp extractor:

```bash
kubectl get pod -n ai llm-serving-0 -o json | jq -r '
{
  pod: .metadata.name,
  created: .metadata.creationTimestamp,
  scheduled: (.status.conditions[]? | select(.type=="PodScheduled") | .lastTransitionTime),
  initialized: (.status.conditions[]? | select(.type=="Initialized") | .lastTransitionTime),
  ready: (.status.conditions[]? | select(.type=="Ready") | .lastTransitionTime),
  model_loaded: (.status.conditions[]? | select(.type=="ai.example.com/ModelLoaded") | .lastTransitionTime),
  warmup_done: (.status.conditions[]? | select(.type=="ai.example.com/WarmupDone") | .lastTransitionTime)
}'
```

Publish stage durations as custom histograms, for example
`ai_pod_startup_seconds_bucket{stage=...}`.

Prometheus recording rule example:

```yaml
groups:
  - name: ai-startup
    rules:
      - record: ai:pod_startup_seconds:p95
        expr: |
          histogram_quantile(
            0.95,
            sum(rate(ai_pod_startup_seconds_bucket[5m])) by (le, stage, model)
          )
```

### 5) Tie SLO directly to rollout gate and rollback

Example rollout guard: rollback when warmup P95 breaches threshold.

```bash
QUERY='ai:pod_startup_seconds:p95{stage="warmup",model="llama-3-8b"}'
P95=$(curl -sG "http://prometheus.monitoring:9090/api/v1/query" \
  --data-urlencode "query=${QUERY}" | jq -r '.data.result[0].value[1]')

awk "BEGIN {exit !(${P95} < 45)}" || {
  echo "warmup p95=${P95}s > 45s, rollback"
  kubectl rollout undo deploy/llm-serving -n ai
  exit 1
}
```

This converts “observe after release” into “enforce during release.”

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
