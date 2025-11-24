---
status: Active
maintainer: pacoxu
last_updated: 2025-11-24
tags: kubernetes, scalability, large-scale, api-server, etcd
canonical_path: docs/kubernetes/large-scale-clusters.md
---

# Large-Scale Kubernetes Clusters

This document covers the key technologies and architectural patterns that enable
massive Kubernetes clusters at scale. It discusses proven approaches from
various implementations, including Google's 130,000-node GKE cluster and other
large-scale deployments.

## Overview

Large-scale Kubernetes clusters (10,000+ nodes) present unique challenges in
areas such as API server performance, storage backend scalability, network
resource management, and distributed storage. This guide explores the
technologies and patterns that address these challenges.

**Key Resources:**

- [How Google Does It: Building the largest known Kubernetes cluster, with
  130,000 nodes](https://cloud.google.com/blog/products/containers-kubernetes/how-we-built-a-130000-node-gke-cluster/)
  ([Chinese translation](https://mp.weixin.qq.com/s/Cp9X574wpMnJsPAasPpkVw))
- [A Huge Cluster or Multi-Clusters: Identifying the Bottleneck](https://github.com/user-attachments/files/23701506/A.Huge.Cluster.or.Multi-Clusters_.Identifying.the.Bottleneck.rc.2.pptx)
  - Presentation discussing bottlenecks and architectural decisions for
    large-scale deployments

## Key Technologies

### 1. Consistent Reads from Cache (KEP-2340)

**Status**: Implemented in Kubernetes

**Problem**: At massive scale, etcd becomes a bottleneck as the Kubernetes API
server needs to handle millions of read requests. Traditional architecture
requires all reads to go through etcd, creating performance and scalability
limitations.

**Solution**: KEP-2340 introduces a caching layer in the API server that allows
consistent reads to be served directly from the cache without hitting etcd.
This dramatically reduces the load on etcd while maintaining consistency
guarantees.

**Key Features**:

- **Watch-based cache**: The API server maintains a watch on all resources
  and keeps the cache up-to-date
- **Consistency guarantees**: Ensures that reads from cache are consistent
  with the actual state in etcd
- **Resource versioning**: Uses resource versions to detect stale reads
- **Reduced etcd load**: Significantly reduces read pressure on etcd cluster

**Benefits for Large-Scale Clusters**:

- Enables handling of millions of API requests without overwhelming etcd
- Improves overall cluster responsiveness
- Reduces etcd cluster size requirements
- Allows horizontal scaling of API servers

**References**:

- [KEP-2340: Consistent Reads from Cache](https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/2340-Consistent-reads-from-cache)
- [Kubernetes API Server Caching](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/)

### 2. Snapshottable API Server Cache (KEP-4988)

**Status**: In development/Alpha

**Problem**: When API servers restart or scale up, they need to rebuild their
entire cache by listing all resources from etcd. At 130,000-node scale, this
initial cache population can take significant time and creates a massive
spike in etcd load.

**Solution**: KEP-4988 introduces the ability to snapshot the API server cache
and restore it on startup, dramatically reducing the time and load required
to bring new API servers online.

**Key Features**:

- **Fast cache restoration**: New API servers can start serving requests
  within seconds instead of minutes
- **Reduced etcd load**: Eliminates the need for massive LIST operations
  during API server startup
- **Persistent storage**: Cache snapshots can be stored in object storage
  (GCS, S3, etc.)
- **Incremental updates**: After restoring from snapshot, API servers only
  need to catch up on changes since the snapshot

**Benefits for Large-Scale Clusters**:

- Faster API server scaling and recovery
- Reduced impact of API server restarts on cluster stability
- Lower etcd resource requirements during scaling events
- Improved cluster resilience and availability

**Implementation Details**:

- Snapshot format includes resource versions for consistency
- Supports incremental snapshot updates
- Compatible with existing watch-based cache mechanisms
- Can be combined with Consistent Reads from Cache for maximum efficiency

**References**:

- [KEP-4988: Snapshottable API Server Cache](https://github.com/kubernetes/enhancements/issues/4988)

### 3. DRANET (Dynamic Resource Allocation for Networking)

**Status**: Part of the broader DRA initiative

**Problem**: Traditional Kubernetes networking assumes relatively simple
network requirements. At massive scale with AI/ML workloads, clusters need
sophisticated network resource management including RDMA, SR-IOV, and
specialized networking devices.

**Solution**: DRANET extends the Dynamic Resource Allocation (DRA) framework
to networking resources, enabling fine-grained allocation and management of
network devices and capabilities.

**Key Features**:

- **Network device management**: Treats network devices as first-class
  resources in Kubernetes
- **RDMA support**: Enables efficient RDMA (Remote Direct Memory Access)
  allocation for high-performance AI/ML workloads
- **SR-IOV integration**: Manages SR-IOV virtual functions for network
  isolation
- **Topology awareness**: Considers network topology when scheduling pods
- **Multi-network support**: Allows pods to request multiple network
  interfaces with different characteristics

**Benefits for Large-Scale Clusters**:

- Essential for AI/ML training workloads requiring high-bandwidth, low-latency
  networking
- Enables efficient use of specialized network hardware
- Supports complex multi-tenant networking requirements
- Improves performance predictability for network-intensive workloads

**Use Cases in Large-Scale Clusters**:

- GPU-to-GPU communication for distributed training
- High-throughput data ingestion pipelines
- Low-latency inference serving
- Multi-tenant network isolation

**References**:

- [Kubernetes Dynamic Resource Allocation](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [KEP-3063: Dynamic Resource Allocation](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/3063-dynamic-resource-allocation)
- See also: [DRA Documentation](./dra.md)

### 4. Scalable Storage Backends (Spanner and Alternatives)

**Problem**: etcd, while excellent for most Kubernetes deployments, has
practical limits on cluster size. At very large scales (50,000+ nodes), the
number of resources and watch streams can exceed what a traditional etcd
cluster can handle efficiently.

**Solutions**: Several approaches exist for scaling beyond etcd limitations:

#### Google Cloud Spanner

**Status**: Production-ready, Google Cloud-specific

Google Cloud uses Cloud Spanner as an alternative backend for the Kubernetes
API server, replacing etcd for data storage while maintaining API compatibility.

**Key Features**:

- **Massive scalability**: Spanner is designed to scale to millions of nodes
  and petabytes of data
- **Global distribution**: Supports multi-region deployments with strong
  consistency
- **Automatic sharding**: Data is automatically distributed across many
  servers
- **No manual scaling**: Scales automatically based on load
- **Strong consistency**: Provides linearizable reads and writes like etcd

**Benefits for Large-Scale Clusters**:

- Removes etcd as a scalability bottleneck
- Enables clusters far beyond typical Kubernetes size limits
- Provides better availability and disaster recovery
- Reduces operational overhead of managing etcd clusters

**Comparison with etcd**:

| Feature | etcd | Cloud Spanner |
| --- | --- | --- |
| Maximum cluster size | ~5,000 nodes (practical) | 100,000+ nodes |
| Scaling | Manual, limited | Automatic, unlimited |
| Multi-region | Requires federation | Native support |
| Operational overhead | High at scale | Low (managed service) |
| Cost | Infrastructure only | Pay-per-use |

**Technical Details**:

- Uses the same API server interface as etcd
- Implements watch mechanism compatible with Kubernetes expectations
- Optimized for Kubernetes access patterns (many watches, few writes)
- Integrates with Consistent Reads from Cache for maximum performance

#### Alternative Approaches

While Spanner is Google Cloud-specific, other organizations use different
approaches for scaling beyond etcd:

- **TiKV**: Cloud-native distributed key-value store with compatibility layer
  for Kubernetes
- **Multi-cluster Federation**: Split workloads across multiple smaller
  clusters rather than a single massive cluster
- **Optimized etcd Configuration**: Careful tuning of etcd parameters,
  dedicated high-performance hardware, and strategic sharding

**Note**: The choice between a single large cluster and multiple smaller
clusters depends on workload characteristics, operational complexity, and
cost considerations. See the presentation "[A Huge Cluster or Multi-Clusters:
Identifying the Bottleneck](https://github.com/user-attachments/files/23701506/A.Huge.Cluster.or.Multi-Clusters_.Identifying.the.Bottleneck.rc.2.pptx)"
for more details on this trade-off.

**References**:

- [Cloud Spanner](https://cloud.google.com/spanner)
- [Kubernetes API Server Storage Interface](https://kubernetes.io/docs/concepts/overview/kubernetes-api/)

### 5. High-Performance Distributed Storage (Lustre and Alternatives)

**Status**: Multiple open-source and commercial solutions available

**Problem**: At large scale with AI/ML workloads, clusters need to handle
massive amounts of data for model training, inference, and checkpointing.
Traditional storage solutions cannot provide the required throughput and IOPS.

**Solutions**: Several high-performance distributed file systems are used in
large-scale Kubernetes deployments:

#### Lustre

Lustre provides a high-performance distributed file system optimized for
large-scale parallel I/O workloads, making it ideal for AI/ML clusters running
on Kubernetes.

**Key Features**:

- **Parallel I/O**: Multiple clients can read/write to the same file
  simultaneously
- **High throughput**: Can achieve hundreds of GB/s aggregate throughput
- **Massive scale**: Supports clusters with thousands of nodes and petabytes
  of data
- **POSIX compliance**: Works with standard file system APIs
- **Flexible architecture**: Separate metadata and object storage servers

**Architecture Components**:

- **Metadata Servers (MDS)**: Manage file namespace and permissions
- **Object Storage Servers (OSS)**: Store actual file data
- **Clients**: Mount Lustre file system and access data
- **Management Server (MGS)**: Coordinates cluster configuration

**Benefits for Large-Scale AI Clusters**:

- **Training data access**: Enables efficient loading of training datasets
  across thousands of GPUs
- **Checkpoint storage**: Fast checkpoint writes during distributed training
- **Model storage**: High-performance model artifact storage and versioning
- **Shared storage**: Multiple pods can access the same data simultaneously

**Kubernetes Integration**:

- **CSI Driver**: Third-party Lustre CSI drivers available for dynamic volume
  provisioning
- **StatefulSets**: Supports stable, persistent storage for training jobs
- **Persistent Volumes**: Standard PV/PVC interface for Lustre volumes
- **ReadWriteMany**: Supports RWX access mode for shared datasets

**Use Cases in 130K-node Cluster**:

1. **Distributed Training**: Shared access to training datasets across
   multiple nodes
2. **Checkpointing**: High-speed checkpoint writes for fault tolerance
3. **Model Registry**: Centralized storage for trained models
4. **Data Preprocessing**: Parallel data transformation pipelines
5. **Inference Caching**: Shared cache for model artifacts

**Performance Characteristics**:

- **Sequential read**: 100+ GB/s aggregate throughput
- **Random I/O**: Millions of IOPS across cluster
- **Metadata operations**: Tens of thousands of ops/second
- **Scalability**: Linear performance scaling with additional servers

**Comparison with Other Storage Solutions**:

| Feature | Lustre | NFS | Ceph | Local SSDs |
| --- | --- | --- | --- | --- |
| Throughput | Very High | Low | Medium | Very High |
| IOPS | Very High | Low | Medium | Very High |
| Scalability | Excellent | Poor | Good | N/A |
| Shared Access | Yes | Yes | Yes | No |
| Complexity | High | Low | Medium | Low |
| Use Case | HPC/AI Training | General | General | Node-local |

**Deployment Considerations**:

- **Network requirements**: Requires high-bandwidth, low-latency network
  (InfiniBand or 100GbE+)
- **Server sizing**: MDS and OSS nodes need adequate resources
- **Client configuration**: Proper tuning for Kubernetes workloads
- **Monitoring**: Comprehensive monitoring of Lustre components
- **Backup strategy**: Regular snapshots and disaster recovery planning

**Alternative Solutions**:

For organizations not using Lustre, similar capabilities can be achieved with:

- **WekaFS**: Modern parallel file system with similar performance
- **BeeGFS**: Alternative parallel file system popular in HPC
- **IBM Spectrum Scale (GPFS)**: Enterprise-grade parallel file system
- **Cloud-native**: Object storage (S3, GCS) with client-side caching

**References**:

- [Lustre File System](https://www.lustre.org/)
- [Lustre Documentation](https://doc.lustre.org/)
- [High-Performance Storage in Kubernetes](https://kubernetes.io/blog/2019/01/15/container-storage-interface-ga/)

## Architectural Patterns for Large-Scale Clusters

### Multi-API Server Architecture

Running multiple API server instances with load balancing:

- **Load balancer**: Distributes requests across API servers
- **Health checking**: Removes unhealthy API servers from rotation
- **Cache coherence**: Ensures consistency across API server caches
- **Graceful scaling**: Add/remove API servers without disruption

### Resource Partitioning

Divide the cluster into logical partitions:

- **Namespace isolation**: Separate workload types
- **Node pools**: Dedicated nodes for specific workload types
- **Priority classes**: Ensure critical workloads get resources
- **Resource quotas**: Prevent any tenant from consuming all resources

## Best Practices for Large-Scale Clusters

### 1. Monitoring and Observability

- **Metrics aggregation**: Use efficient metric collection (e.g., Prometheus
  federation)
- **Distributed tracing**: Track requests across components
- **Log aggregation**: Centralized logging with proper retention
- **Alerting**: Proactive alerting on performance degradation

### 2. Upgrade Strategies

- **Rolling upgrades**: Upgrade API servers and nodes incrementally
- **Canary testing**: Test upgrades on small subset first
- **Automated validation**: Verify cluster health after each step
- **Rollback capability**: Quick rollback mechanism for failures

### 3. Security at Scale

- **RBAC optimization**: Efficient role-based access control
- **Network policies**: Segment traffic between workloads
- **Admission controllers**: Enforce security policies
- **Audit logging**: Track all API server access

### 4. Performance Optimization

- **API server tuning**: Optimize cache size, rate limiting
- **etcd/Spanner optimization**: Proper storage backend configuration
- **Network optimization**: Use fast networks for control plane
- **Client-side caching**: Reduce API server load with informers

## Future Directions

### Ongoing Improvements

- **Enhanced caching**: Further optimizations to API server caching
- **Better sharding**: Distribute load more efficiently
- **Storage backends**: More options beyond etcd and Spanner
- **Observability**: Better visibility into cluster internals

### Community Initiatives

- [SIG Scalability](https://github.com/kubernetes/community/tree/master/sig-scalability):
  Working on Kubernetes scalability improvements
- [Scalability SLIs/SLOs](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md):
  Defining performance targets for large clusters

## References

### Blog Posts and Articles

- [How Google Does It: Building the largest known Kubernetes cluster, with
  130,000 nodes](https://cloud.google.com/blog/products/containers-kubernetes/how-we-built-a-130000-node-gke-cluster/)
- [Chinese Translation (微信公众号)](https://mp.weixin.qq.com/s/Cp9X574wpMnJsPAasPpkVw)

### Kubernetes Enhancement Proposals (KEPs)

- [KEP-2340: Consistent Reads from Cache](https://github.com/kubernetes/enhancements/tree/master/keps/sig-api-machinery/2340-Consistent-reads-from-cache)
- [KEP-4988: Snapshottable API Server Cache](https://github.com/kubernetes/enhancements/issues/4988)
- [KEP-3063: Dynamic Resource Allocation](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/3063-dynamic-resource-allocation)

### Official Documentation

- [Kubernetes Scalability](https://kubernetes.io/docs/setup/best-practices/cluster-large/)
- [API Server Configuration](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/)
- [Cloud Spanner Documentation](https://cloud.google.com/spanner/docs)
- [Lustre Documentation](https://doc.lustre.org/)

### Related Topics

- [Scheduling Optimization](./scheduling-optimization.md)
- [Dynamic Resource Allocation](./dra.md)
- [Pod Startup Speed](./pod-startup-speed.md)

---

**Note**: This documentation is based on publicly available information from
Google's blog posts and Kubernetes community resources. Specific
implementation details may vary. Always refer to official documentation for
production deployments.
