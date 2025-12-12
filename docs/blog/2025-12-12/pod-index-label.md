---
status: Active
maintainer: pacoxu
date: 2025-12-12
tags: kubernetes, kep-4017, pod-index-label, co-evolving, statefulset, indexed-jobs, lws
canonical_path: docs/blog/2025-12-12/pod-index-label.md
---

# Pod Index Label: Enabling Smarter Workload Orchestration in Kubernetes

## Co-Evolving: When Small Kubernetes Features Unlock Big Ecosystem Innovations

In the world of AI infrastructure, we often focus on the latest GPUs, the
fastest inference engines, or the most sophisticated training frameworks. But
sometimes, the most impactful improvements come from small, foundational
features that enable the entire ecosystem to evolve. This is the essence of
**Co-Evolving** (协同演进) — when Kubernetes core capabilities enable
downstream projects to innovate in ways previously impossible or impractical.

Today, we explore [KEP-4017: Pod Index
Label](https://github.com/kubernetes/enhancements/tree/master/keps/sig-apps/4017-pod-index-label),
a seemingly simple feature that has reached GA in Kubernetes 1.32 (December
2024) and is already transforming how AI workloads are orchestrated, monitored,
and scaled.

## The Problem: Pod Index Was Hidden

Before KEP-4017, Kubernetes workloads that used indexed pods faced a surprising
limitation:

### StatefulSets

StatefulSet pods have always had an ordinal index (0, 1, 2, ...) as part of
their pod name (e.g., `web-0`, `web-1`, `web-2`). However, this index was only
available by **parsing the pod name** — a hacky solution that made it difficult
to:

- Use the pod index in environment variables via the Downward API
- Filter metrics and logs by pod index
- Route traffic to a specific pod (e.g., always send requests to `web-0`)
- Select pods by index using label selectors

### Indexed Jobs

Indexed Jobs (introduced in Kubernetes 1.24) assign a completion index to each
pod, but this index was only set as an **annotation** (`batch.kubernetes.io/
job-completion-index`), not a label. This meant:

- You couldn't select pods by index using `kubectl` or API queries
- Service selectors couldn't target specific pod indices
- Observability tools couldn't easily filter by pod index

## The Solution: Pod Index as a Label

KEP-4017 introduces a simple but powerful change: **the pod index is now set as
a label** on pods for both StatefulSets and Indexed Jobs.

### Implementation Details

| Workload Type | Label Key | Label Value | Example |
| --- | --- | --- | --- |
| **StatefulSet** | `apps.kubernetes.io/pod-index` | Pod ordinal (0, 1, 2, ...) | `apps.kubernetes.io/pod-index: "0"` |
| **Indexed Job** | `batch.kubernetes.io/job-completion-index` | Completion index | `batch.kubernetes.io/job-completion-index: "5"` |

The label is set at **pod creation time** by the respective controllers:

- The StatefulSet controller adds `apps.kubernetes.io/pod-index` during pod
  creation
- The Job controller adds `batch.kubernetes.io/job-completion-index` for
  Indexed Jobs (in addition to the existing annotation)

### Rollout Strategy

To avoid disrupting existing workloads, KEP-4017 follows a **non-disruptive
rollout strategy**:

- **Newly created pods** get the label automatically
- **Existing pods** are not modified (no retroactive labeling)
- This means an existing StatefulSet or Indexed Job may have some pods with the
  label and some without until pods are recreated

This design prioritizes stability over immediate consistency, which is the
right trade-off for production Kubernetes clusters.

### Timeline

- **2023-05-17**: KEP published
- **Kubernetes 1.28** (August 2023): Feature entered **Beta** with feature gate
  `PodIndexLabel` enabled by default
- **Kubernetes 1.32** (December 2024): Feature graduated to **GA** (General
  Availability)

## Use Case: LeaderWorkerSet (LWS) with Leader as Pod-0

One of the most compelling use cases for pod index labels is in **LeaderWorker
architectures**, exemplified by the [LeaderWorkerSet
(LWS)](https://github.com/kubernetes-sigs/lws) project.

### What is LeaderWorkerSet?

LeaderWorkerSet is a Kubernetes workload API (currently in SIG Apps) designed
for distributed applications that require leader-follower patterns:

- One **leader pod** coordinates the workload
- Multiple **worker pods** execute tasks under the leader's coordination
- All pods need to start together (gang scheduling)
- The leader needs a stable identity and discoverable address

### The Challenge: Defining Leader vs. Worker

In traditional setups, leader and worker pods were often managed in separate
resources:

- **Option 1**: Separate Deployments — but this makes gang scheduling and
  coordination difficult
- **Option 2**: Separate StatefulSets — but this adds operational complexity
- **Option 3**: Single StatefulSet with conditional logic — but how does each
  pod know if it's the leader or a worker?

### The Solution: Leader as Pod-0, Workers Starting from Pod-1

With pod index labels, LWS can define a single StatefulSet where:

- **Pod with index 0** (`apps.kubernetes.io/pod-index: "0"`) is the **leader**
- **Pods with index ≥ 1** (`apps.kubernetes.io/pod-index: "1"`, `"2"`, ...)
  are **workers**

#### Co-Evolving with KEP-3335: StatefulSet Start Ordinal

But there's more to this story! LWS doesn't just use KEP-4017 (Pod Index Label)
— it also leverages [KEP-3335: StatefulSet Start
Ordinal](https://github.com/kubernetes/enhancements/tree/master/keps/sig-apps/3335-statefulset-slice),
another foundational Kubernetes feature that reached GA in Kubernetes 1.31
(August 2024).

**KEP-3335** allows StatefulSets to start from a **custom ordinal** instead of
always starting at 0. This is controlled by the `spec.ordinals.start` field:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: workers
spec:
  ordinals:
    start: 1  # Start worker pods from index 1
  replicas: 9   # Creates pods 1-9
```

**Why this matters for LWS:**

LeaderWorkerSet can create **two separate StatefulSets**:

1. **Leader StatefulSet**: 1 replica, starting at ordinal 0 (default)
2. **Worker StatefulSet**: N replicas, starting at ordinal 1 (using
   `spec.ordinals.start: 1`)

This architecture provides:

- **Clean separation**: Leader and workers have distinct lifecycle management
- **Independent scaling**: Scale workers without affecting the leader
- **Consistent indexing**: Workers are numbered 1, 2, 3... (not 0, 1, 2...)
- **Service targeting**: Use pod index labels to route traffic appropriately

#### Example: LWS with Separate Leader and Worker StatefulSets

```yaml
# Service targeting only the leader (pod-0)
apiVersion: v1
kind: Service
metadata:
  name: ml-training-leader
spec:
  selector:
    app: ml-training
    apps.kubernetes.io/pod-index: "0"  # Only select the leader pod
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
---
# Leader StatefulSet: 1 replica at ordinal 0
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: ml-training-leader
spec:
  serviceName: "ml-training"
  replicas: 1  # Just the leader
  selector:
    matchLabels:
      app: ml-training
      role: leader
  template:
    metadata:
      labels:
        app: ml-training
        role: leader
    spec:
      containers:
      - name: trainer
        image: ml-training:latest
        env:
        - name: POD_INDEX
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['apps.kubernetes.io/pod-index']
        - name: ROLE
          value: "leader"
---
# Worker StatefulSet: 9 replicas starting from ordinal 1
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: ml-training-worker
spec:
  serviceName: "ml-training"
  ordinals:
    start: 1  # Workers start from pod-1 (KEP-3335)
  replicas: 9   # Creates pods 1-9
  selector:
    matchLabels:
      app: ml-training
      role: worker
  template:
    metadata:
      labels:
        app: ml-training
        role: worker
    spec:
      containers:
      - name: trainer
        image: ml-training:latest
        env:
        - name: POD_INDEX
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['apps.kubernetes.io/pod-index']
        - name: ROLE
          value: "worker"
        - name: LEADER_ADDRESS
          value: "ml-training-leader:8080"
```

**Result**: You get pods `ml-training-leader-0` (leader), `ml-training-worker-1`,
`ml-training-worker-2`, ..., `ml-training-worker-9` (workers), all with
consistent `apps.kubernetes.io/pod-index` labels for easy targeting and
discovery.

#### The Power of Co-Evolving Features

This example perfectly illustrates the **co-evolving** theme:

1. **KEP-3335** (StatefulSet Start Ordinal, GA in K8s 1.31) enables workers to
   start from ordinal 1
2. **KEP-4017** (Pod Index Label, GA in K8s 1.32) exposes these ordinals as
   labels for easy selection
3. **LWS** combines both features to create an elegant leader-worker architecture

Neither feature alone would enable this pattern as cleanly:

- Without KEP-3335, workers would be numbered 0, 1, 2... (conflicting with the
  leader)
- Without KEP-4017, you couldn't easily create a Service targeting only pod-0
  or filter logs/metrics by pod index

Together, they unlock a powerful pattern that's now being adopted across the
Kubernetes AI/ML ecosystem.

#### Alternative: Single StatefulSet with Conditional Logic

For simpler cases, you can also use a **single StatefulSet** where pod-0 is the
leader and pods 1+ are workers:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: ml-training
spec:
  replicas: 10  # 1 leader + 9 workers
  template:
    spec:
      containers:
      - name: trainer
        env:
        - name: POD_INDEX
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['apps.kubernetes.io/pod-index']
        - name: IS_LEADER
          value: "$([ \"$POD_INDEX\" -eq 0 ] && echo true || echo false)"
```

This is simpler but less flexible than the two-StatefulSet approach with
KEP-3335.

### Why This Matters for AI Workloads

#### 1. Distributed Training with Parameter Servers

In distributed training architectures like TensorFlow Parameter Server or
PyTorch Elastic:

- **Pod-0** acts as the parameter server or master coordinator
- **Pods 1-N** are training workers
- The parameter server needs a stable, discoverable address
- Workers need to know their rank/index for gradient aggregation

With pod index labels:

- Create a Service that selects only `apps.kubernetes.io/pod-index: "0"`
- Workers discover the parameter server via DNS (`ml-training-leader.default.
  svc.cluster.local`)
- Each worker reads its own index from the Downward API to determine its rank

#### 2. Inference with Prefill-Decode Disaggregation

In modern LLM inference architectures (see [P/D Disaggregation](../../inference/
pd-disaggregation.md)), workloads are split into:

- **Prefill workers**: Generate initial KV cache from prompts
- **Decode workers**: Generate tokens autoregressively

LWS-inspired architectures like those used in
[llm-d](https://github.com/llm-d/llm-d) leverage pod index labels to:

- Route requests to pod-0 (the coordinator)
- Dynamically schedule prefill vs. decode work based on pod indices
- Monitor and collect metrics per pod index for performance tuning

#### 3. Multi-Replica Model Serving

In multi-model serving scenarios:

- **Pod-0**: Serves the primary production model
- **Pods 1-N**: Serve A/B test variants or shadow models

With pod index labels, traffic routing becomes trivial:

```yaml
# Production traffic goes to pod-0
apiVersion: v1
kind: Service
metadata:
  name: model-production
spec:
  selector:
    app: model-server
    apps.kubernetes.io/pod-index: "0"
---
# Experimental traffic goes to pod-1
apiVersion: v1
kind: Service
metadata:
  name: model-experiment
spec:
  selector:
    app: model-server
    apps.kubernetes.io/pod-index: "1"
```

## Beyond LWS: Other Use Cases

### 1. Ray Clusters

[Ray](https://github.com/ray-project/ray) is a distributed computing framework
for AI/ML workloads. Ray clusters have:

- **Head node** (pod-0): Manages the cluster, schedules tasks
- **Worker nodes** (pods 1-N): Execute distributed computations

With pod index labels, Ray operators can:

- Create a headless Service targeting only the head node
- Configure workers to discover the head node via DNS
- Monitor head node metrics separately from worker metrics

### 2. Observability: Filtering Logs and Metrics

Scenario: A distributed training job with 1000 workers fails. You want to check
if the failure originated from a specific pod index.

**Before KEP-4017**:

```bash
# Painful: fetch logs from all pods, grep for pod names
kubectl logs -l app=training --prefix | grep "training-42"
```

**After KEP-4017**:

```bash
# Elegant: filter by pod index label
kubectl logs -l app=training,apps.kubernetes.io/pod-index=42
```

This extends to Prometheus metrics:

```promql
# Query metrics only from the leader pod
sum(gpu_utilization{pod_index="0"})

# Compare metrics across worker indices
sum by (pod_index) (training_loss{pod_index=~"[1-9].*"})
```

### 3. Chaos Engineering and Testing

With pod index labels, chaos engineering tools like [Chaos
Mesh](https://chaos-mesh.org/) can target specific pod indices:

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: test-leader-failure
spec:
  selector:
    labelSelectors:
      "apps.kubernetes.io/pod-index": "0"  # Kill the leader pod
  mode: one
  action: pod-kill
```

This enables reproducible testing of failure scenarios:

- What happens if the leader pod dies?
- How does the system behave if worker-5 experiences network latency?

### 4. Rolling Deployments and Blue-Green Testing

For StatefulSets that need rolling updates with manual validation:

- Update pod-0 first, validate metrics
- If successful, roll out to pods 1-N
- If failed, revert only pod-0

This is now easily scriptable:

```bash
# Update only pod-0 for canary testing
kubectl patch statefulset web --type='json' -p='[{"op": "replace", "path":
"/spec/template/spec/containers/0/image", "value":"new-image:v2"}]'
kubectl delete pod web-0  # Only restart pod-0

# Monitor pod-0 metrics
kubectl top pod -l apps.kubernetes.io/pod-index=0

# If successful, update the rest
kubectl rollout restart statefulset web
```

## Technical Impact: Minimal Changes, Maximum Value

One of the beautiful aspects of KEP-4017 is its **minimal implementation
complexity**:

### StatefulSet Controller Changes

The fix in the StatefulSet controller was a [simple addition of one
label](https://github.com/kubernetes/kubernetes/pull/119232):

```go
// In newStatefulSetPod() function
pod.Labels[apps.StatefulSetPodIndexLabel] = strconv.Itoa(index)
```

### Job Controller Changes

Similarly, the Job controller [added one
line](https://github.com/kubernetes/kubernetes/pull/119232) to set the label
alongside the existing annotation.

### Size Impact

The label adds **approximately 40 bytes** per pod:

- Label key: `apps.kubernetes.io/pod-index` (29 bytes)
- Label value: `"<index>"` (1-6 bytes for indices 0-999999)
- Total: ~30-35 bytes per pod

For a cluster with 150,000 pods (Kubernetes scalability limit), this adds:

- **~6 MB** of additional etcd storage
- Negligible impact on API server memory

This is an excellent example of how **small, well-designed features can unlock
disproportionate value** for the ecosystem.

## The Co-Evolving Story

KEP-4017 exemplifies the **Co-Evolving** philosophy:

1. **Kubernetes Core** identifies a gap in foundational capabilities
2. **Community** discusses use cases across SIGs (Apps, Batch, Node)
3. **Simple enhancement** is proposed with minimal disruption
4. **Downstream projects** (LWS, Ray, inference platforms) adopt the feature
5. **Entire ecosystem** benefits from improved orchestration, observability, and
   efficiency

This is not a flashy feature that gets headline attention, but it's the kind of
**thoughtful, incremental improvement** that makes Kubernetes the de facto
platform for AI workloads.

## KEP-3335: StatefulSet Start Ordinal — More Use Cases

While we've focused on how KEP-3335 enables leader-worker patterns with LWS,
this feature has several other powerful use cases:

### 1. StatefulSet Migration Across Namespaces or Clusters

KEP-3335's primary motivation was enabling **zero-downtime StatefulSet
migration**. Consider migrating a 5-replica StatefulSet from namespace `shared`
to namespace `app-team`:

**Phase 1: Initial state**

```yaml
# In namespace: shared
name: my-app
replicas: 5
ordinals.start: 0
# Pods: my-app-0, my-app-1, my-app-2, my-app-3, my-app-4
```

**Phase 2: Migrate pods 3-4**

```yaml
# In namespace: shared
name: my-app
replicas: 3
ordinals.start: 0
# Pods: my-app-0, my-app-1, my-app-2
---
# In namespace: app-team
name: my-app
replicas: 2
ordinals.start: 3  # Start from pod-3
# Pods: my-app-3, my-app-4
```

**Phase 3: Complete migration**

Scale down the source StatefulSet and scale up the destination iteratively,
maintaining pod ordinals throughout. This preserves application identity and
data references.

### 2. 1-Based Indexing for Clarity

Some applications prefer 1-based indexing (where pod-1 is the first pod, not
pod-0):

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: database
spec:
  ordinals:
    start: 1  # Pods numbered 1, 2, 3, 4, 5
  replicas: 5
```

**Benefits**:

- Natural alignment with human counting ("5 replicas" = pods 1-5, not 0-4)
- Easier for non-technical stakeholders to understand
- Some legacy applications expect 1-based numbering

### 3. Partitioning StatefulSets Across Failure Domains

You can split a large StatefulSet across multiple failure domains by creating
separate StatefulSets with non-overlapping ordinal ranges:

```yaml
# Availability Zone 1
name: my-app-az1
replicas: 100
ordinals.start: 0
# Pods: 0-99
---
# Availability Zone 2
name: my-app-az2
replicas: 100
ordinals.start: 100
# Pods: 100-199
---
# Availability Zone 3
name: my-app-az3
replicas: 100
ordinals.start: 200
# Pods: 200-299
```

With KEP-4017's pod index labels, you can now easily:

- Route traffic to specific AZ ranges using Services with label selectors
- Monitor and alert on per-AZ metrics using `apps.kubernetes.io/pod-index`
- Implement sophisticated failover logic based on pod index ranges

### 4. Reserved Ordinals for Special Purposes

You can reserve specific ordinal ranges for different purposes:

```yaml
# Control plane pods: ordinals 0-2
name: app-control
replicas: 3
ordinals.start: 0
---
# Data plane pods: ordinals 10-109
name: app-data
replicas: 100
ordinals.start: 10
---
# Monitoring pods: ordinals 200-204
name: app-monitor
replicas: 5
ordinals.start: 200
```

This creates clear separation and makes it easy to target specific pod groups
using the `apps.kubernetes.io/pod-index` label.

## Looking Forward: Future Possibilities

With pod index labels now stable in Kubernetes 1.32, we can expect:

### 1. Enhanced Workload APIs

- **JobSet**: Could leverage pod index labels for sub-job coordination
- **LWS**: Already incorporating pod index labels for leader election and
  service discovery
- **New CRDs**: Future workload controllers can build on this foundation

### 2. Smarter Scheduling

- **Topology-aware scheduling**: Place pod-0 on a high-bandwidth node
- **Heterogeneous resources**: Assign more GPU memory to pod-0 (parameter
  server)
- **Preemption policies**: Protect pod-0 from preemption in low-priority jobs

### 3. AI Gateway Integration

AI gateways like [Envoy AI Gateway](https://github.com/envoyproxy/ai-gateway)
and [Gateway API Inference
Extension](https://github.com/kubernetes-sigs/gateway-api-inference-extension)
can:

- Route requests to specific pod indices for A/B testing
- Implement sticky sessions based on pod index
- Load-balance across worker indices while excluding the leader

### 4. Improved Observability

Observability platforms (Prometheus, Grafana, OpenTelemetry) can:

- Provide pod index as a first-class dimension in dashboards
- Detect anomalies in specific pod indices
- Correlate pod index with hardware topology (NUMA, GPU affinity)

## How to Use It Today

### Check Your Kubernetes Version

Pod index labels are available in:

- **Kubernetes 1.28+** (Beta, feature gate enabled by default)
- **Kubernetes 1.32+** (GA, always enabled)

```bash
kubectl version --short
```

### Verify Labels on Existing Workloads

```bash
# For StatefulSets
kubectl get pods -l app=your-statefulset -o yaml | grep pod-index

# For Indexed Jobs
kubectl get pods -l job-name=your-job -o yaml | grep job-completion-index
```

### Create a New StatefulSet with Pod Index Awareness

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: distributed-training
spec:
  serviceName: "training"
  replicas: 4
  selector:
    matchLabels:
      app: training
  template:
    metadata:
      labels:
        app: training
    spec:
      containers:
      - name: trainer
        image: pytorch/pytorch:latest
        env:
        - name: POD_INDEX
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['apps.kubernetes.io/pod-index']
        - name: WORLD_SIZE
          value: "4"
        - name: IS_MASTER
          value: "$([ \"$POD_INDEX\" -eq 0 ] && echo true || echo false)"
```

### Create Services Targeting Specific Indices

```yaml
# Service for the master node (pod-0)
apiVersion: v1
kind: Service
metadata:
  name: training-master
spec:
  selector:
    app: training
    apps.kubernetes.io/pod-index: "0"
  ports:
  - port: 29500
    name: master-port
---
# Service for all workers (pod-1, pod-2, pod-3)
apiVersion: v1
kind: Service
metadata:
  name: training-workers
spec:
  selector:
    app: training
  ports:
  - port: 29500
    name: worker-port
```

## Conclusion: Small Features, Big Impact

KEP-4017 is a perfect example of how **foundational Kubernetes enhancements
enable ecosystem innovation**. By exposing the pod index as a label, Kubernetes
has:

- **Simplified leader-worker architectures** like LeaderWorkerSet
- **Improved observability** for distributed AI workloads
- **Enabled smarter traffic routing** for model serving
- **Streamlined testing and chaos engineering**

This is the essence of **Co-Evolving**: Kubernetes doesn't need to solve every
AI infrastructure challenge directly. Instead, it provides the right primitives
— and the ecosystem builds the solutions.

As you design your next AI infrastructure platform, consider:

- How can you leverage pod index labels for leader election?
- Can you simplify your orchestration logic by using pod-0 as a coordinator?
- Are your metrics and logs filterable by pod index?

The feature is here, it's stable, and it's ready to unlock your next innovation.

## References

### Kubernetes Enhancement Proposals (KEPs)

- [KEP-4017: Pod Index
  Label](https://github.com/kubernetes/enhancements/tree/master/keps/sig-apps/4017-pod-index-label)
  — Adds pod index as a label for StatefulSets and Indexed Jobs (GA in K8s 1.32)
- [KEP-3335: StatefulSet Start
  Ordinal](https://github.com/kubernetes/enhancements/tree/master/keps/sig-apps/3335-statefulset-slice)
  — Enables custom start ordinals for StatefulSets (GA in K8s 1.31)

### Official Documentation

- [Kubernetes StatefulSets
  Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Kubernetes Indexed
  Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Pod Index Label GA
  Announcement](https://kubernetes.io/blog/2024/12/17/statefulset-podindexlabel-ga/)
- [StatefulSet Start Ordinal Blog Post (Chinese)](https://kubernetes.io/zh-cn/blog/2023/04/28/statefulset-start-ordinal/)

### Projects and Use Cases

- [LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws) — Kubernetes
  SIG Apps project for leader-worker patterns
- [LWS Gang Scheduling
  KEP](https://github.com/kubernetes-sigs/lws/blob/main/keps/407-gang-scheduling/README.md)
- [Prefill-Decode Disaggregation Guide](../../inference/pd-disaggregation.md)

---

*This blog post is part of the AI-Infra learning series, focused on how
Kubernetes and cloud-native technologies are evolving to support modern AI
workloads.*
