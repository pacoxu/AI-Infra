---
status: Active
maintainer: pacoxu
date: 2025-11-24
tags: kubernetes, scheduling, gang-scheduling, workload-api, batch-processing
canonical_path: docs/blog/2025-11-25/gang-scheduling.md
---

# Gang Scheduling Comes to Kubernetes: A Game Changer for AI/ML Workloads

## Introduction

Scheduling large workloads in Kubernetes has always been challenging. When you
need to run distributed training jobs, batch processing tasks, or other
multi-pod applications, the traditional pod-by-pod scheduling approach can lead
to resource wastage, deadlocks, and inefficiencies. Today, we're excited to
share insights about the **Workload Aware Scheduling** initiative that's
transforming how Kubernetes handles multi-pod workloads.

## The Problem with Traditional Pod Scheduling

In traditional Kubernetes scheduling, each pod is scheduled independently. For
distributed workloads like:

- **Distributed ML training** (e.g., PyTorch, TensorFlow multi-worker jobs)
- **Batch processing** (e.g., Apache Spark, Ray clusters)
- **High-performance computing** (e.g., MPI applications)

This independent scheduling creates several problems:

1. **Partial scheduling deadlocks**: Some pods get scheduled while others wait
   indefinitely for resources
2. **Resource wastage**: Scheduled pods consume resources but can't start work
   until all peers are ready
3. **Poor cluster utilization**: Resources are tied up by incomplete workloads
4. **Unpredictable job completion times**: Jobs may wait hours or days in
   partially-scheduled states

## Kubernetes v1.35: Workload Aware Scheduling

The Kubernetes community has introduced **Workload Aware Scheduling** in
v1.35, featuring three major components:

### 1. Workload API (Alpha)

The new `Workload` API resource in `scheduling.k8s.io/v1alpha1` provides a
structured way to define scheduling requirements for multi-pod applications.

```yaml
apiVersion: scheduling.k8s.io/v1alpha1
kind: Workload
metadata:
  name: training-job-workload
  namespace: ml-workloads
spec:
  podGroups:
  - name: workers
    policy:
      gang:
        # All-or-nothing: schedule only if 4 pods can run together
        minCount: 4
```

Link your pods to the workload:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: worker-0
  namespace: ml-workloads
spec:
  workloadRef:
    name: training-job-workload
    podGroup: workers
  containers:
  - name: trainer
    image: my-ml-framework:latest
    resources:
      requests:
        nvidia.com/gpu: 1
```

### 2. Gang Scheduling (Alpha)

Gang scheduling implements the **all-or-nothing** placement strategy:

**How it works:**

1. **Waiting Phase**: When pods arrive, the scheduler blocks them until
   `minCount` pods are pending
2. **Evaluation Phase**: The scheduler attempts to find suitable nodes for all
   pods in the gang
3. **Decision Phase**:
   - ✅ **Success**: If all pods can be placed, they're bound to nodes together
   - ❌ **Failure**: If any pod can't be placed within timeout (5 minutes),
      ALL pods are rejected and requeued

This prevents resource waste and ensures your distributed workload either runs
completely or waits for sufficient resources.

**Key benefits:**

- Eliminates partial scheduling deadlocks
- Improves cluster utilization by freeing resources for runnable workloads
- Provides predictable behavior for distributed applications
- Works seamlessly with pod preemption and autoscaling

### 3. Opportunistic Batching (Beta)

Opportunistic Batching is a performance optimization that speeds up scheduling
of identical pods without requiring any configuration changes.

**How it works:**

When the scheduler processes pods with identical scheduling requirements
(same resources, images, affinities, etc.), it can reuse feasibility
calculations and scoring results for subsequent pods in the queue.

**Performance impact:**

- Dramatically reduces scheduling latency for large homogeneous workloads
- Can improve scheduling throughput by 5-10x for batch workloads
- Works transparently - no user configuration needed
- Enabled by default in Kubernetes v1.35 (Beta)

**Current restrictions:**

- Disabled for pods using topology spread constraints
- Disabled for pods using Dynamic Resource Allocation (DRA)
- All scheduling-relevant pod fields must be identical

## Real-World Use Cases

### Distributed ML Training

```yaml
apiVersion: scheduling.k8s.io/v1alpha1
kind: Workload
metadata:
  name: pytorch-training
spec:
  podGroups:
  - name: workers
    policy:
      gang:
        minCount: 8  # Need 8 GPUs for distributed training
```

Your PyTorch distributed training job only starts when all 8 workers can be
scheduled, preventing wasted GPU resources.

### Apache Spark on Kubernetes

```yaml
apiVersion: scheduling.k8s.io/v1alpha1
kind: Workload
metadata:
  name: spark-job
spec:
  podGroups:
  - name: executors
    policy:
      gang:
        minCount: 10  # 1 driver + 9 executors minimum
```

Spark jobs with gang scheduling avoid the common problem where the driver
starts but executors can't be scheduled.

### Ray Clusters

Ray applications benefit from gang scheduling by ensuring the head node and
worker nodes start together, enabling immediate distributed computation.

## The Roadmap: What's Coming in 1.36 and Beyond

The Workload Aware Scheduling effort has an ambitious roadmap for Kubernetes
1.36:

### Planned for v1.36

- **Expanding Workload API**: Enhanced capabilities and refinements based on
  alpha feedback
- **Auto-workload for Job, StatefulSet, JobSet**: Automatic workload creation
  for common Kubernetes resources
- **Topology Aware Scheduling**: Consider network and hardware topology when
  placing gang members
- **Single-cycle workload scheduling**: Schedule entire gangs in a single
  scheduling cycle for better performance
- **Tree-based workload scheduling algorithm**: More efficient gang placement
  decisions
- **Improved binding process**: Better handling of kubelet races using
  nominations
- **Delayed preemption**: Introduce nominating victims before actual eviction
- **Workload-level preemption**: Preempt entire gangs rather than individual
  pods

### Long-term Vision

The ultimate goal is to make Kubernetes natively understand and optimize for
workload-level operations, including:

- Deep integration with cluster autoscaling
- Workload-aware resource quotas and limits
- Better support for mixed workload types (batch + serving)
- Enhanced observability for multi-pod applications

## Upcoming Official Blog Post

The Kubernetes community is preparing an official blog post about Workload
Aware Scheduling that will be published soon on the Kubernetes blog. Watch for
[kubernetes/website#53012](https://github.com/kubernetes/website/pull/53012)
to be merged for the official announcement.

## Getting Started

### Prerequisites

- Kubernetes v1.35 or later
- Feature gates configured on kube-apiserver and kube-scheduler

### Enable Workload API and Gang Scheduling

```bash
# On kube-apiserver
--feature-gates=GenericWorkload=true
--runtime-config=scheduling.k8s.io/v1alpha1=true

# On kube-scheduler
--feature-gates=GenericWorkload=true,GangScheduling=true
```

### Enable Opportunistic Batching

Opportunistic Batching is **enabled by default** in v1.35 as a Beta feature.
To disable it:

```bash
# On kube-scheduler
--feature-gates=OpportunisticBatching=false
```

### Testing Gang Scheduling

1. Create a Workload resource
2. Create pods with `workloadRef` pointing to the Workload
3. Observe scheduling behavior in kube-scheduler logs
4. Monitor metrics for gang scheduling success/failure rates

## Best Practices

1. **Set appropriate minCount**: Consider your application's minimum viable
   size
2. **Use resource requests accurately**: Gang scheduling depends on accurate
   resource requirements
3. **Monitor scheduling metrics**: Track gang scheduling success rates and
   timeout events
4. **Test with cluster autoscaling**: Ensure your autoscaler can provision
   nodes for gangs
5. **Plan for failure scenarios**: Understand timeout behavior and retry logic

## Comparison with Existing Solutions

Before native gang scheduling, users relied on:

- **Volcano**: CNCF incubating project with gang scheduling
- **Kueue**: Kubernetes SIG project for queue and quota management
- **YuniKorn**: Apache project with gang scheduling support
- **Custom schedulers**: In-house solutions for specific use cases

**Why use native gang scheduling?**

- Maintained by Kubernetes SIG Scheduling
- Integrated with core scheduler features (preemption, autoscaling)
- No additional components to deploy and maintain
- Part of the Kubernetes conformance suite (eventually)

**When to use external schedulers?**

- Need production-ready gang scheduling today (use Volcano or Kueue)
- Require features beyond current Kubernetes roadmap
- Have existing investments in specific schedulers

## Resources and References

### KEPs and Documentation

- [KEP-4671: Gang Scheduling](https://github.com/kubernetes/enhancements/issues/4671)
- [KEP-5598: Opportunistic Batching](https://github.com/kubernetes/enhancements/blob/master/keps/sig-scheduling/5598-opportunistic-batching/README.md)
- [Workload Aware Scheduling Tracking Issue](https://github.com/kubernetes/kubernetes/issues/132192)
- [Kubernetes Website PR #53012](https://github.com/kubernetes/website/pull/53012)

### Related Projects

- [Volcano Scheduler](https://github.com/volcano-sh/volcano) - CNCF Incubating
- [Kueue](https://github.com/kubernetes-sigs/kueue) - Kubernetes SIG Project
- [YuniKorn](https://yunikorn.apache.org/) - Apache Project

### Community

- SIG Scheduling: <https://github.com/kubernetes/community/tree/master/sig-scheduling>
- Slack: #sig-scheduling on Kubernetes Slack

## Conclusion

Gang Scheduling and Workload Aware Scheduling represent a major step forward
for Kubernetes in supporting AI/ML, HPC, and batch processing workloads. The
v1.35 alpha release provides a foundation for native multi-pod scheduling,
with an exciting roadmap for v1.36 and beyond.

We encourage the community to:

- Test these features in development environments
- Provide feedback through GitHub issues
- Share use cases and requirements
- Contribute to the ongoing development

The future of Kubernetes scheduling is workload-aware, and the journey has
just begun!

---

**Author**: AI Infrastructure Learning Path  
**Date**: November 24, 2025  
**Tags**: #kubernetes #scheduling #gangscheduling #ai-ml #batch-processing
