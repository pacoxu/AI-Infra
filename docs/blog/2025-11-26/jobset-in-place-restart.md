---
status: Active
maintainer: pacoxu
date: 2025-11-26
tags: kubernetes, jobset, in-place-restart, co-evolving, batch-processing
canonical_path: docs/blog/2025-11-26/jobset-in-place-restart.md
---

# JobSet In-Place Restart: From 2m10s to 10s — A 92% Speed Boost

## Co-Evolving: When Kubernetes Features Empower the Ecosystem

In the rapidly evolving AI infrastructure landscape, a beautiful synergy is
emerging: the Kubernetes community develops foundational capabilities, and
downstream projects like [JobSet](https://github.com/kubernetes-sigs/jobset),
[Ray](https://github.com/ray-project/ray), and
[LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws) adopt these
features to dramatically improve their efficiency. We call this **Co-Evolving**
(协同演进) — the entire ecosystem advancing together.

Kubernetes has been introducing more AI-related capabilities recently, but
realizing their full potential in AI workloads requires adaptation by other
projects. Today, we'll explore a prime example: **JobSet leveraging Kubernetes
In-Place Container Restart to achieve 92% faster restart times**.

## The Problem: Slow JobSet Restart

When a distributed training job running on
[JobSet](https://github.com/kubernetes-sigs/jobset) needs to restart (due to
transient failures, configuration updates, or checkpoint recovery), the
traditional approach involves:

1. **Delete all pods** in the JobSet
2. **Wait for pod termination** to complete
3. **Reschedule all pods** through the Kubernetes scheduler
4. **Wait for pod startup** (including image pulls, init containers, etc.)

In a large-scale cluster with 5000 nodes, this process takes approximately
**2 minutes and 10 seconds**. For AI/ML workloads where fast recovery is
critical, this overhead is significant.

## The Solution: In-Place Container Restart

Kubernetes has introduced capabilities that allow containers to restart without
pod recreation:

### KEP-5307: Container Restart Policy (Kubernetes 1.34)

[KEP-5307](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5307-container-restart-policy/README.md)
introduces fine-grained control over individual container restart behavior
within pods. This allows:

- Specifying restart policies per container (not just per pod)
- Triggering container restarts without affecting the entire pod
- Maintaining pod identity, IP, and volumes during container restarts

### KEP-5532: Restart All Containers on Container Exits (Kubernetes 1.35)

[KEP-5532](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5532-restart-all-containers-on-container-exits/README.md)
extends this capability to enable coordinated restarts:

- Restart all containers in a pod when specific containers exit
- Restart init containers and sidecars as part of the pod lifecycle
- Enable pod-level restart coordination without pod recreation

## Real-World Results: JobSet In-Place Restart

The JobSet team has developed an
[in-place restart prototype](https://github.com/kubernetes-sigs/jobset/compare/main...GiuseppeTT:jobset:in-place-restart-prototype)
that demonstrates remarkable performance improvements:

| Metric | Traditional Restart | In-Place Restart | Improvement |
| --- | --- | --- | --- |
| Restart Time | 2m10s | 10s | **92% faster** |
| Test Scale | 5000 nodes | 5000 nodes | - |
| Scheduling Overhead | High | None | Eliminated |
| Pod Recreation | Required | Not needed | Avoided |

For detailed design information, see the
[JobSet in-place restart design document](https://docs.google.com/document/d/16zexVooHKPc80F4dVtUjDYK9DOpkVPRNfSv0zRtfFpk/edit?tab=t.0#heading=h.y6xl7juq7465).

## Why This Matters for AI Workloads

### 1. Distributed Training Recovery

Large-scale distributed training jobs (PyTorch DDP, TensorFlow MultiWorkerMirroredStrategy)
are particularly sensitive to restart latency:

- **Checkpoint recovery**: After a failure, all workers need to restart from
  the latest checkpoint. In-place restart gets workers back online 12x faster.
- **Gradient synchronization**: All workers must be running for training to
  proceed. Faster restarts mean less wasted GPU time.
- **Cost savings**: On expensive GPU clusters ($2-10/GPU-hour), 2 minutes saved
  per restart adds up significantly.

### 2. Job Dependencies

Many AI pipelines have complex job dependencies. When a job restarts:

- **Downstream jobs** wait for upstream completion
- **Gang scheduling constraints** require all workers to be present
- **Network connectivity** must be maintained for collective operations

In-place restart preserves pod identity and network connectivity, minimizing
disruption to the overall pipeline.

### 3. Resource Efficiency

Traditional restart involves:

- **Scheduler load**: Finding nodes for potentially thousands of pods
- **API server load**: Creating/deleting pod objects
- **Node preparation**: Image pulls, volume mounts, init containers

In-place restart eliminates all of this overhead, keeping resources available
for actual workloads.

## How It Works

### Before: Traditional Restart Flow

```text
Job Restart Triggered
    ↓
Delete All Pods → Wait for Termination (30s+)
    ↓
Create New Pods → Wait for Scheduling (30s+)
    ↓
Pull Images (if needed) → Start Containers (60s+)
    ↓
Total: ~2m10s
```

### After: In-Place Restart Flow

```text
Job Restart Triggered
    ↓
Signal Container Exit → Container Restarts In-Place (10s)
    ↓
Total: ~10s
```

The key differences:

1. **No pod deletion**: Pod objects remain, preserving identity
2. **No rescheduling**: Pods stay on their current nodes
3. **No image pulls**: Images are already cached on nodes
4. **Immediate restart**: Container process simply restarts

## Implementation Considerations

### When to Use In-Place Restart

- **Transient failures**: Container crashes, OOM kills, network timeouts
- **Configuration updates**: Restart to pick up new environment variables
- **Checkpoint recovery**: Resume training from saved state
- **Rolling updates**: Graceful restart of workers in sequence

### When Traditional Restart is Needed

- **Node failures**: Pod must move to a healthy node
- **Resource changes**: Pod needs more/less resources (consider VPA)
- **Image updates**: New container image required
- **Topology changes**: Pod needs different placement

### Integration with JobSet

JobSet can leverage in-place restart through:

```yaml
apiVersion: jobset.x-k8s.io/v1alpha2
kind: JobSet
metadata:
  name: distributed-training
spec:
  replicatedJobs:
  - name: workers
    replicas: 8
    template:
      spec:
        template:
          spec:
            restartPolicy: Always  # Enables in-place restart
            containers:
            - name: trainer
              image: pytorch/pytorch:latest
```

## The Broader Co-Evolving Pattern

This JobSet improvement exemplifies the Co-Evolving pattern in cloud-native AI:

| Kubernetes Capability | Project Adoption | Benefit |
| --- | --- | --- |
| In-Place Restart | JobSet | 92% faster recovery |
| Gang Scheduling (1.35) | Kueue, LWS | All-or-nothing placement |
| DRA (1.34 GA) | NVIDIA GPU Operator | Flexible device allocation |
| Workload API (1.35) | Volcano, YuniKorn | Native workload support |

As Kubernetes continues to add AI-friendly features, we expect more projects
to adopt them, creating a virtuous cycle of improvement.

## Getting Started

### Prerequisites

- Kubernetes 1.34+ (for KEP-5307)
- Kubernetes 1.35+ (for KEP-5532 pod-level restart)
- JobSet with in-place restart support (check latest releases)

### Enable Feature Gates

```bash
# On kube-apiserver and kubelet
--feature-gates=InPlacePodVerticalScaling=true

# For 1.35+ pod-level restart features
--feature-gates=SidecarContainers=true
```

### Test In-Place Restart

1. Deploy a JobSet with `restartPolicy: Always`
2. Trigger a container restart (e.g., `kubectl exec ... -- kill -TERM 1`)
3. Observe the restart time compared to pod recreation

## Future Roadmap

The in-place restart capability continues to evolve:

- **KEP-5307 graduation**: Moving toward Beta/GA
- **KEP-5532 graduation**: Enhanced pod-level restart control
- **JobSet integration**: Native support for in-place restart policies
- **Monitoring**: Better observability for restart events
- **Kueue integration**: Workload-aware restart handling

## Conclusion

The JobSet in-place restart optimization demonstrates the power of Co-Evolving
in the Kubernetes ecosystem. By adopting upstream Kubernetes capabilities,
projects can achieve dramatic performance improvements:

- **92% faster restart** (2m10s → 10s)
- **No scheduling overhead**
- **Preserved pod identity and network**
- **Reduced API server load**

This is just one example of how the Kubernetes community and downstream
projects work together to improve AI workload efficiency. As more AI-related
features land in Kubernetes, we can expect even more optimizations from
projects like JobSet, Ray, LWS, and others.

The future of AI infrastructure is Co-Evolving — and it's happening now.

---

## References

### KEPs and Documentation

- [KEP-5307: Container Restart Policy](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5307-container-restart-policy/README.md)
- [KEP-5532: Restart All Containers on Container Exits](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5532-restart-all-containers-on-container-exits/README.md)
- [KEP-1287: In-Place Pod Vertical Scaling](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/1287-in-place-update-pod-resources/README.md)
- [JobSet In-Place Restart Design Document](https://docs.google.com/document/d/16zexVooHKPc80F4dVtUjDYK9DOpkVPRNfSv0zRtfFpk/edit?tab=t.0#heading=h.y6xl7juq7465)
- [JobSet In-Place Restart Prototype](https://github.com/kubernetes-sigs/jobset/compare/main...GiuseppeTT:jobset:in-place-restart-prototype)

### Related Projects

- [JobSet](https://github.com/kubernetes-sigs/jobset) - Kubernetes SIG Apps
- [LeaderWorkerSet](https://github.com/kubernetes-sigs/lws) - Kubernetes SIG Apps
- [Kueue](https://github.com/kubernetes-sigs/kueue) - Kubernetes SIG Scheduling
- [Volcano](https://github.com/volcano-sh/volcano) - CNCF Incubating

### Related Blog Posts

- [Gang Scheduling in Kubernetes](./gang-scheduling.md)
- [Scheduling Optimization](../../kubernetes/scheduling-optimization.md)

---

**Author**: AI Infrastructure Learning Path  
**Date**: November 26, 2025  
**Tags**: #kubernetes #jobset #in-place-restart #co-evolving #ai-infrastructure
