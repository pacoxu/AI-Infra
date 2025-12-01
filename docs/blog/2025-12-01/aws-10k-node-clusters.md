---
status: Active
maintainer: pacoxu
date: 2025-12-01
tags: kubernetes, large-scale, aws, eks, scalability, etcd, image-pull
canonical_path: docs/blog/2025-12-01/aws-10k-node-clusters.md
---

# AWS 10K Node EKS Ultra Scale Clusters: Under the Hood

Following our previous coverage of
[Google's 130K node cluster](../../kubernetes/large-scale-clusters.md), this
post explores how Amazon EKS achieves ultra-scale with 10,000+ nodes. Based on
the AWS blog post
[Under the Hood: Amazon EKS Ultra Scale Clusters](https://aws.amazon.com/blogs/containers/under-the-hood-amazon-eks-ultra-scale-clusters/),
we'll examine both community optimizations and AWS-specific innovations.

## Overview

AWS EKS Ultra Scale Clusters target AI/ML workloads requiring massive compute
capacity. The key challenges at this scale include:

- **API Server pressure**: Handling millions of requests
- **etcd performance**: Storage backend bottlenecks
- **Image distribution**: Fast container image pulls across thousands of nodes
- **Scheduling efficiency**: Pod placement at scale
- **Observability**: Monitoring and scaling supporting services

**Performance SLOs** at AWS scale:

| Operation | Target Latency |
| --- | --- |
| GET/PUT requests | < 1 second |
| LIST requests | < 30 seconds |
| Scheduler throughput | 500 pods/second |

## Part 1: Community Improvements

Before diving into AWS-specific optimizations, let's examine upstream
Kubernetes improvements that benefit all large-scale deployments.

### Consistent Reads from Cache (Kubernetes v1.33)

**Problem**: At scale, every API server read hitting etcd creates unsustainable
load.

**Solution**: Kubernetes v1.33 introduces improvements to the API server
caching layer, enabling more reads to be served directly from cache while
maintaining consistency guarantees.

**Key Features**:

- Watch-based cache keeps data synchronized with etcd
- Resource versioning ensures consistency
- Significantly reduced etcd read load

**Impact**: Clusters can handle millions of API requests without overwhelming
etcd. For implementation details, see
[KEP-2340: Consistent Reads from Cache](https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/2340-Consistent-reads-from-cache).

### Karpenter: Just-in-Time Node Provisioning

[Karpenter](https://github.com/kubernetes-sigs/karpenter) is a Kubernetes node
provisioner that provides:

- **Rapid scaling**: Provisions nodes in seconds, not minutes
- **Right-sizing**: Selects optimal instance types for pending pods
- **Cost optimization**: Automatically consolidates workloads
- **Multi-arch support**: Handles ARM and x86 instances seamlessly

**Why Karpenter matters at scale**:

Traditional Cluster Autoscaler requires pre-defined node groups and can be slow
to react. Karpenter directly watches for pending pods and provisions exactly
the right instances, significantly reducing time-to-schedule.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: ai-workloads
spec:
  template:
    spec:
      requirements:
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["p5.48xlarge", "p4d.24xlarge"]
      expireAfter: 720h
```

**Community alternatives**:

- **Cluster Autoscaler**: Traditional approach, works with node groups
- **Koordinator**: Advanced scheduling with QoS guarantees
- **Volcano**: Batch scheduling for AI/ML workloads

## Part 2: AWS-Specific Optimizations

### etcd Backend: Amazon QLDB Journal

**Challenge**: Standard etcd with Raft consensus can become a bottleneck at
ultra-scale, particularly for write-heavy workloads.

**AWS Solution**: Replace Raft with Amazon QLDB (Quantum Ledger Database)
journal for the etcd backend:

| Component | Standard etcd | AWS EKS Ultra Scale |
| --- | --- | --- |
| Consensus | Raft | Amazon QLDB Journal |
| Write throughput | Limited by Raft | Higher throughput |
| Durability | Disk-based | Managed ledger |
| Operational overhead | Self-managed | AWS-managed |

**How it works**:

1. etcd writes go to QLDB journal instead of local disk
2. QLDB provides append-only, immutable storage
3. Consistency maintained through QLDB's transaction model

**Community alternatives**:

- **Spanner** (Google): Used in GKE for 130K+ nodes
- **TiKV** with kubebrain: ByteDance's approach for 20K nodes
- **Kine**: Lightweight alternative using MySQL/PostgreSQL

### etcd BoltDB on tmpfs

**Problem**: BoltDB (etcd's storage engine) performance degrades under heavy
I/O load.

**Solution**: Mount BoltDB storage on tmpfs (memory-based filesystem):

- **Benefit**: Eliminates disk I/O latency
- **Trade-off**: Requires sufficient memory, data persistence handled by QLDB
- **Result**: Dramatically faster etcd operations

This technique is particularly effective when combined with the QLDB journal,
as durability is guaranteed by QLDB while performance comes from memory-based
operations.

### Image Pull Acceleration: SOCI Snapshotter

At 10K nodes, container image distribution becomes a critical bottleneck. AWS
uses [SOCI (Seekable OCI)](https://github.com/awslabs/soci-snapshotter) for
lazy-loading container images.

**How SOCI works**:

1. **Index generation**: Create seekable index for container images
2. **Lazy loading**: Containers start immediately, pulling layers on-demand
3. **Background fetch**: Remaining layers download while container runs

**Performance impact**:

| Image Size | Traditional Pull | SOCI Lazy Load | Improvement |
| --- | --- | --- | --- |
| 1 GB | ~30 seconds | ~2 seconds | 93% faster |
| 5 GB | ~150 seconds | ~3 seconds | 98% faster |
| 10 GB | ~300 seconds | ~5 seconds | 98% faster |

**Community alternatives**:

| Solution | Approach | Use Case |
| --- | --- | --- |
| **SOCI** | Lazy loading | AWS, large images |
| **Nydus** | Lazy loading | General, Dragonfly integration |
| **Stargz** | Lazy loading | containerd native |
| **Dragonfly** | P2P distribution | Large clusters, bandwidth limited |
| **Spegel** | P2P distribution | Lightweight, cluster-local |
| **Kraken** | P2P distribution | Uber, extreme scale |

For more on image optimization, see
[Pod Startup Speed](../../kubernetes/pod-startup-speed.md#image-optimization).

### CoreDNS Autoscaler

**Problem**: DNS queries scale with cluster size. At 10K nodes, CoreDNS can
become overwhelmed.

**Solution**: Proportional CoreDNS autoscaling based on cluster size:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: coredns
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: coredns
  minReplicas: 2
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

**Best practices**:

- Scale CoreDNS pods proportionally to node count
- Use NodeLocal DNSCache to reduce CoreDNS load
- Monitor DNS latency as a key SLI

### LWS + vLLM for LLM Inference

For large language model inference at scale, AWS recommends:

**[LeaderWorkerSet (LWS)](https://github.com/kubernetes-sigs/lws)**:

- Manages groups of pods with leader-worker topology
- Enables efficient distributed inference
- Provides stable network identities

**[vLLM](https://github.com/vllm-project/vllm)**:

- High-throughput LLM serving engine
- PagedAttention for efficient memory use
- Continuous batching for better GPU utilization

**Example deployment**:

```yaml
apiVersion: leaderworkerset.x-k8s.io/v1
kind: LeaderWorkerSet
metadata:
  name: vllm-inference
spec:
  replicas: 4
  leaderWorkerTemplate:
    size: 8
    leaderTemplate:
      spec:
        containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          resources:
            limits:
              nvidia.com/gpu: 8
```

For more on inference optimization, see the
[Inference Guide](../../inference/README.md).

## Comparison: AWS vs Google vs Community

| Optimization | AWS EKS | Google GKE | Community |
| --- | --- | --- | --- |
| **Storage backend** | QLDB journal | Spanner | TiKV, Kine |
| **Read caching** | API server cache | Consistent reads | KEP-2340 |
| **Image acceleration** | SOCI | gcr.io optimization | Nydus, Dragonfly |
| **Node provisioning** | Karpenter | GKE Autopilot | Cluster Autoscaler |
| **DNS scaling** | CoreDNS autoscaler | Custom | NodeLocal DNS |
| **Target scale** | 10K nodes | 130K nodes | 5K nodes (default) |

## Implementation Recommendations

### For Production Deployments

1. **Start with community optimizations**:
   - Enable consistent reads from cache
   - Use Karpenter or Cluster Autoscaler
   - Implement image lazy loading (Nydus/Stargz)

2. **Add platform-specific features**:
   - AWS: SOCI, managed etcd backends
   - GKE: Spanner backend, native optimizations
   - On-premises: TiKV, optimized etcd clusters

3. **Monitor key SLIs**:
   - API server latency (p99 < 1s for GETs)
   - etcd latency and disk I/O
   - Scheduler throughput
   - DNS query latency

### Architecture Overview

```text
┌─────────────────────────────────────────────────────────┐
│                    Control Plane                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │API Server│  │API Server│  │     API Server       │  │
│  │ (cache)  │  │ (cache)  │  │      (cache)         │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│       │             │                    │              │
│       └─────────────┼────────────────────┘              │
│                     │                                    │
│              ┌──────▼──────┐                            │
│              │ etcd cluster │                           │
│              │ (QLDB/tmpfs) │                           │
│              └──────────────┘                           │
├─────────────────────────────────────────────────────────┤
│                    Data Plane                           │
│  ┌────────┐ ┌────────┐ ┌────────┐        ┌────────┐   │
│  │Node 1  │ │Node 2  │ │Node 3  │  ...   │Node 10K│   │
│  │(SOCI)  │ │(SOCI)  │ │(SOCI)  │        │(SOCI)  │   │
│  └────────┘ └────────┘ └────────┘        └────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Conclusion

AWS EKS Ultra Scale Clusters demonstrate that 10K+ node Kubernetes deployments
are achievable through a combination of:

- **Upstream improvements**: Consistent reads, better caching
- **Storage optimization**: Alternative backends, memory-based storage
- **Image acceleration**: Lazy loading with SOCI
- **Intelligent scaling**: Karpenter, CoreDNS autoscaling
- **Workload optimization**: LWS + vLLM for AI inference

While AWS and Google take different approaches (QLDB vs Spanner, SOCI vs native
optimization), the underlying principles are similar: reduce pressure on etcd,
accelerate image distribution, and optimize scheduling.

For organizations building large-scale Kubernetes clusters, the key is to start
with community best practices and layer on platform-specific optimizations as
needed.

---

## References

### AWS Resources

- [Under the Hood: Amazon EKS Ultra Scale Clusters](https://aws.amazon.com/blogs/containers/under-the-hood-amazon-eks-ultra-scale-clusters/)
- [SOCI Snapshotter](https://github.com/awslabs/soci-snapshotter)
- [Karpenter](https://github.com/kubernetes-sigs/karpenter)

### Community Resources

- [KEP-2340: Consistent Reads from Cache](https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/2340-Consistent-reads-from-cache)
- [Large Cluster Best Practices](https://kubernetes.io/docs/setup/best-practices/cluster-large/)
- [SIG Scalability](https://github.com/kubernetes/community/tree/master/sig-scalability)

### Related Documentation

- [Large-Scale Kubernetes Clusters](../../kubernetes/large-scale-clusters.md)
- [Pod Startup Speed](../../kubernetes/pod-startup-speed.md)
- [Inference Guide](../../inference/README.md)

---

**Author**: AI Infrastructure Learning Path
**Date**: December 1, 2025
**Tags**: #kubernetes #aws #eks #large-scale #etcd #image-pull
