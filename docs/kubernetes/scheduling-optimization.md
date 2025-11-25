---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: kubernetes, scheduling, optimization, large-scale
canonical_path: docs/kubernetes/scheduling-optimization.md
---

# Large Clusters Scheduling Optimization

This guide provides comprehensive strategies for optimizing scheduling
performance and resource utilization in large-scale Kubernetes clusters,
particularly for AI/ML workloads. Large clusters (1000+ nodes, 10000+ pods)
require specialized scheduling techniques to maintain performance and maximize
resource utilization.

## Why Scheduling Optimization Matters

Efficient scheduling is critical for:

- **High throughput**: Supporting rapid pod creation (1000+ pods/s)
- **Resource efficiency**: Maximizing GPU/CPU utilization (>80%)
- **Cost optimization**: Reducing idle resources and over-provisioning
- **SLA compliance**: Meeting latency and availability requirements
- **Fairness**: Ensuring equitable resource distribution across tenants

## Overview

Scheduling optimization focuses on two key dimensions:

1. **Performance**: Throughput, latency, and API responsiveness
2. **Resource Utilization**: Efficient allocation, load balancing, and
   bin-packing

---

## 1. Performance Optimization

### 1.1 High Throughput Scheduling

**Challenge**: Default Kubernetes scheduler processes ~100 pods/s, insufficient
for large-scale batch workloads.

**Solutions:**

#### Optimistic Concurrency

- **Concept**: Schedule multiple pods concurrently assuming resources are
  available, handle conflicts via retry
- **Trade-offs**: Higher throughput but potential conflicts when resources are
  limited
- **Best for**: Clusters with abundant resources and diverse pod requirements

**Example Projects:**

- <a href="https://github.com/kubewharf/godel-scheduler">`Godel Scheduler`</a>:
  ByteDance scheduler achieving 5000 pods/s with optimistic concurrency and
  multi-level scheduling queues

#### Multi-Scheduler Architecture

- **Concept**: Run multiple scheduler instances in parallel, each handling
  subset of workloads
- **Strategies**:
  - **Workload-based**: Separate schedulers for batch, serving, training
  - **Tenant-based**: Dedicated schedulers per team/namespace
  - **Priority-based**: Different schedulers for high/low priority workloads
- **Coordination**: Use leader election or partitioning to avoid conflicts

**Example Projects:**

- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>: Kubernetes
  SIG Project supporting multi-queue and quota management
- <a href="https://github.com/volcano-sh/volcano">`Volcano`</a>: CNCF
  Incubating project with gang scheduling and queue management

**Best Practices:**

- Monitor conflict rates; if >10%, reduce concurrency or scheduler count
- Use node affinity/anti-affinity to partition workloads across schedulers
- Configure appropriate cache synchronization intervals (default: 30s)

### 1.2 Multi Node Pool Strategy

**Concept**: Divide cluster nodes into pools, assign schedulers to specific
pools to reduce scheduling conflicts and improve cache locality.

**Node Pool Types:**

- **Dedicated pools**: GPU nodes, inference nodes, training nodes
- **Shared pools**: General-purpose workloads with resource spillover
- **Priority pools**: High-priority workloads with reserved capacity

**Implementation:**

- Use node labels/taints to define pools:
  `node-pool=gpu-training`, `node-pool=cpu-batch`
- Configure scheduler affinity via `nodeSelector` or `nodeAffinity`
- Enable cross-pool scheduling for underutilized resources

**Example Projects:**

- <a href="https://github.com/koordinator-sh/koordinator">`Koordinator`</a>:
  CNCF Sandbox project with colocation and QoS management
- <a href="https://github.com/NVIDIA/grove">`NVIDIA Grove`</a>: Gang
  scheduling for AI workloads with topology awareness

### 1.3 Hierarchical Scheduling

**Concept**: Split scheduling into multiple levels to handle very large
clusters (50,000+ nodes) more efficiently. Each level makes coarser-grained
decisions, narrowing down the search space for subsequent levels.

**Scheduling Levels:**

- **Cluster-level**: Decide which subset of nodes or node pools to consider
  based on workload characteristics and resource availability
- **Pool-level**: Select specific nodes within the chosen pool based on
  topology, resource fit, and affinity rules
- **Node-level**: Final placement decision considering GPU topology, NUMA
  alignment, and other fine-grained constraints

**Benefits for Large-Scale Clusters:**

- Reduces scheduling latency by limiting search space at each level
- Enables specialized scheduling logic at different granularities
- Improves cache locality and reduces API server load
- Supports different scheduling strategies per workload type

**Implementation Patterns:**

- **Pre-filtering**: Use node pools and labels to partition nodes before
  scheduling begins
- **Multi-pass scheduling**: First pass selects regions/zones, second pass
  selects specific nodes
- **Staged decisions**: Apply coarse filters (CPU/memory/GPU count) before
  fine-grained ones (topology, affinity)

**Example Use Case:**

For a 100,000-node cluster with GPU training workloads:

1. **Cluster-level**: Choose GPU node pool based on GPU type requirement
   (A100 vs H100)
2. **Pool-level**: Select availability zone with sufficient capacity and low
   network latency
3. **Node-level**: Place pods considering NVLink topology for optimal
   multi-GPU training

**References:**

- See [Large-Scale Clusters](./large-scale-clusters.md) for additional
  patterns used in massive deployments

### 1.4 API Performance Optimization

**Common Bottlenecks:**

- **etcd latency**: Slow reads/writes impact pod creation
- **API Server load**: High request rates from schedulers, controllers
- **Admission webhooks**: Synchronous validation adds latency
- **Large objects**: Pods with many volumes, env vars slow API operations

**Solutions:**

- **etcd optimization**:
  - Use SSDs for etcd storage (99th percentile latency <10ms)
  - Separate etcd cluster for large deployments (5+ nodes)
  - Enable etcd defragmentation and compaction
- **API Server scaling**:
  - Run multiple API Server replicas (1 per 1000 nodes)
  - Increase request limits: `--max-requests-inflight=3000`,
    `--max-mutating-requests-inflight=1000`
  - Use priority and fairness (APF) to prevent scheduler starvation
- **Admission webhook optimization**:
  - Convert synchronous webhooks to asynchronous where possible
  - Set aggressive timeouts (default: 10s, reduce to 2-3s)
  - Use webhook failure policies: `Ignore` for non-critical validations
  - Cache validation results to avoid repeated calls
- **Object size optimization**:
  - Use ConfigMaps/Secrets instead of inline pod specs
  - Limit number of volumes per pod (<20)
  - Use strategic merge patches for updates

**Monitoring:**

- Track API Server request latency (P95/P99)
- Monitor etcd backend commit duration
- Alert on admission webhook timeouts

### 1.5 Batch Dispatch Optimization

**Concept**: Schedule pods in batches rather than individually to amortize
scheduling overhead and improve throughput.

**Batch Scheduling Strategies:**

- **Fixed batch size**: Schedule N pods at a time (e.g., 100 pods/batch)
- **Time-based batching**: Collect pods for T seconds then schedule together
- **Priority-based batching**: Batch pods by priority class

**Implementation:**

- **Kueue**: Provides workload batching and admission control
- **Volcano**: Supports batch scheduling with job-level queue management
- **Custom controllers**: Implement batch admission using operator pattern

**Best Practices:**

- Batch size should balance throughput vs. latency (50-200 pods)
- Use separate queues for interactive vs. batch workloads
- Monitor queue depth and adjust batch parameters dynamically

---

## 2. Resource Utilization Optimization

### 2.1 Dominant Resource Fairness (DRF)

**Concept**: Fair resource allocation considering multiple resource types
(CPU, memory, GPU, storage, bandwidth) rather than single dimension.

**How DRF Works:**

- Calculate each user's dominant resource (highest utilization percentage)
- Allocate resources to maximize minimum dominant resource share
- Ensures no user is bottlenecked on their dominant resource

**Example**: User A needs 2 CPU + 4 GB, User B needs 1 CPU + 8 GB. In 8 CPU,
32 GB cluster:

- User A's dominant resource: Memory (4/32 = 12.5%)
- User B's dominant resource: Memory (8/32 = 25%)
- DRF allocates to equalize dominant shares

**Implementation:**

- <a href="https://github.com/apache/yunikorn-core">`Apache YuniKorn`</a>:
  Implements DRF for multi-tenant scheduling
- <a href="https://github.com/volcano-sh/volcano">`Volcano`</a>: Supports DRF
  via proportion plugin

**Best Practices:**

- Include GPU memory as separate resource dimension for AI workloads
- Consider network bandwidth for distributed training (RDMA/IB)
- Use weights to prioritize certain resources (e.g., GPU weight = 10x CPU)

### 2.2 Load-Aware Scheduling

**Concept**: Make scheduling decisions based on real-time node load metrics
(CPU usage, memory pressure, GPU utilization) rather than just capacity.

**Metrics to Consider:**

- **CPU**: System load average, CPU usage percentage
- **Memory**: Available memory, memory pressure (page cache, swap)
- **GPU**: GPU utilization, GPU memory usage, temperature
- **Network**: Bandwidth usage, packet drop rate
- **Disk**: I/O wait, disk usage

**Implementation:**

- <a href="https://github.com/koordinator-sh/koordinator">`Koordinator`</a>:
  Real-time load-aware scheduling with node metrics
- <a href="https://github.com/kubewharf/godel-scheduler">`Godel Scheduler`</a>:
  Load-aware scoring with katalyst runtime QoS
- **Trimaran**: Kubernetes scheduler plugin for load-aware scheduling

**Best Practices:**

- Use short metric collection intervals (10-30s) for responsiveness
- Combine requests/limits with load metrics for hybrid scoring
- Set load thresholds to prevent scheduling to overloaded nodes (>80% CPU)
- Consider multi-dimensional load (avoid scheduling to nodes with high CPU
  AND memory pressure)

### 2.3 Bin-Packing Strategies

**Concept**: Pack pods onto fewer nodes to maximize utilization and enable
node consolidation/autoscaling.

**Bin-Packing Algorithms:**

- **Best Fit**: Place pod on node with least remaining capacity after
  allocation
- **First Fit**: Place pod on first node with sufficient capacity
- **Worst Fit**: Place pod on node with most remaining capacity (for spreading)
- **Multi-dimensional bin-packing**: Consider CPU, memory, GPU simultaneously

**Implementation:**

- **Kubernetes Scheduler**: Configure `NodeResourcesBalancedAllocation` and
  `NodeResourcesMostAllocated` plugins
- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>: Supports
  workload packing within quotas
- <a href="https://github.com/koordinator-sh/koordinator">`Koordinator`</a>:
  Colocation and QoS-based bin-packing

**Configuration Example:**

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- pluginConfig:
  - name: NodeResourcesMostAllocated
    args:
      resources:
      - name: cpu
        weight: 1
      - name: memory
        weight: 1
      - name: nvidia.com/gpu
        weight: 10
```

**Trade-offs:**

- **Pro**: Higher utilization, lower costs, easier autoscaling
- **Con**: Reduced blast radius, potential resource contention
- **Best for**: Batch workloads, non-critical services, dev/test environments

### 2.4 Preemption and Priority

**Concept**: Lower priority pods can be evicted to make room for higher
priority pods when resources are scarce.

**Priority Classes:**

- **System-critical**: kube-system components (priority: 2000000000)
- **Business-critical**: Production services (priority: 1000-10000)
- **Standard**: Regular workloads (priority: 0)
- **Best-effort**: Batch jobs, dev workloads (priority: -1000)

**Preemption Policies:**

- **PreemptLowerPriority**: Default, preempt lower priority pods
- **Never**: Disable preemption for specific priority classes
- **Graceful preemption**: Allow grace period for pod termination

**Implementation:**

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-ai-training
value: 10000
globalDefault: false
description: "High priority for critical AI training jobs"
preemptionPolicy: PreemptLowerPriority
```

**Best Practices:**

- Limit number of priority classes (5-7) to avoid complexity
- Use priorities sparingly to prevent cascading preemptions
- Set pod disruption budgets (PDBs) to limit preemption impact
- Monitor preemption metrics and adjust priorities accordingly
- Consider cost of preemption (wasted work) vs. SLA requirements

**Example Projects:**

- <a href="https://github.com/volcano-sh/volcano">`Volcano`</a>: Advanced
  preemption with queue-level priorities
- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>: Preemption
  within cohorts and borrowing limits

### 2.5 Gang Scheduling

**Concept**: All-or-nothing scheduling for distributed workloads. Either all
pods in a group are scheduled or none are, preventing partial scheduling and
deadlocks.

**Use Cases:**

- **Distributed training**: PyTorch/TensorFlow multi-node training
- **MPI jobs**: Tightly-coupled HPC workloads
- **Spark/Ray**: Multi-process compute frameworks

**Gang Scheduling Phases:**

1. **Admission**: Check if resources available for entire gang
2. **Reservation**: Reserve resources for all gang members
3. **Binding**: Schedule all pods simultaneously
4. **Timeout**: Release resources if gang cannot be scheduled within timeout

**Implementation:**

- <a href="https://github.com/volcano-sh/volcano">`Volcano`</a>: PodGroup CRD
  with minMember field for gang scheduling
- <a href="https://github.com/NVIDIA/grove">`NVIDIA Grove`</a>: Gang
  scheduling optimized for NVIDIA GPUs
- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>: Workload
  admission control with gang scheduling
- <a href="https://github.com/kubernetes-sigs/lws">`LeaderWorkerSet (LWS)`</a>:
  Kubernetes SIG Project with gang scheduling support

**Example (Volcano PodGroup):**

```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: PodGroup
metadata:
  name: distributed-training-job
spec:
  minMember: 8  # All 8 pods must be scheduled
  minResources:
    cpu: "64"
    memory: "256Gi"
    nvidia.com/gpu: "8"
  queue: ai-training-queue
```

**Best Practices:**

- Set reasonable gang timeouts (5-15 minutes) to prevent indefinite waiting
- Use elastic gang scheduling (minMember < maxMember) when possible
- Combine with coscheduling plugins for topology-aware placement
- Monitor gang scheduling failures and adjust resource quotas

### 2.6 Topology-Aware Scheduling

**Concept**: Schedule pods considering physical topology (NUMA nodes, PCIe
lanes, network topology) to optimize for locality and bandwidth.

**Topology Dimensions:**

- **NUMA nodes**: CPU and memory locality
- **GPU topology**: NVLink connections, PCIe lanes
- **Network topology**: Rack/zone awareness, RDMA fabric
- **Storage topology**: Local vs. remote storage
- **Rack topology**: Physical rack location for failure domains

**Why Topology Matters for AI Workloads:**

Modern AI workloads are extremely topology-sensitive. Misaligned hardware
topology can degrade performance by 30-50% or more:

- **GPU-to-GPU communication**: NVLink provides 600 GB/s vs 64 GB/s PCIe
- **RDMA/GPU-Direct**: Requires GPU and NIC on same PCIe root
- **NUMA locality**: Cross-NUMA memory access adds 30-50% latency

**Implementation Approaches:**

1. **Device Plugin + Topology Manager**: Traditional approach with limited
   cross-device coordination
2. **Kueue Topology-Aware Scheduling**: Uses node labels for rack/block/host
   topology
3. **Volcano Topology Plugin**: GPU and network topology in gang scheduling
4. **DRA (Dynamic Resource Allocation)**: Rich topology constraints with CEL

**Project Support:**

- <a href="https://github.com/kubernetes/dynamic-resource-allocation/">`DRA
  (Dynamic Resource Allocation)`</a>: Structured parameters for device
  topology (GA in v1.34)
- <a href="https://github.com/google/dranet">`DRANET`</a>: Google's DRA
  implementation for network device topology
- <a href="https://github.com/containerd/nri">`NRI (Node Resource
  Interface)`</a>: Fine-grained device management at runtime
- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>: Topology-aware
  scheduling with node labels
- <a href="https://github.com/volcano-sh/volcano">`Volcano`</a>: Gang scheduling
  with topology plugin
- <a href="https://github.com/NVIDIA/KAI-Scheduler">`NVIDIA KAI Scheduler`</a>:
  GPU-optimized topology-aware scheduling
- **Kubernetes Topology Manager**: NUMA-aware pod placement

**DRA Topology Coordination (GPU + NIC):**

DRA enables coordinating multiple device types on the same topology domain:

```yaml
apiVersion: resource.k8s.io/v1beta1
kind: ResourceClaimTemplate
metadata:
  name: gpu-nic-topology
spec:
  spec:
    devices:
      requests:
      - name: gpu
        deviceClassName: nvidia-gpu
        count: 1
      - name: rdma-nic
        deviceClassName: rdma-nic
        count: 1
      constraints:
      # GPU and NIC must be on the same PCIe root
      - requests: ["gpu", "rdma-nic"]
        matchAttribute: pcieRoot
```

**Kueue Topology Labels:**

```yaml
# Standard topology labels used by Kueue and DRANET
cloud.google.com/gce-topology-block: "block-1"
cloud.google.com/gce-topology-subblock: "subblock-1"
cloud.google.com/gce-topology-host: "host-1"
kubernetes.io/hostname: "node-1"
```

**Topology Aware Scenarios:**

- **Multi-GPU training**: Schedule pods to nodes with NVLink/NVSwitch for
  fast GPU-to-GPU communication
- **RDMA workloads**: Place pods on nodes with InfiniBand connectivity and
  GPU-Direct support
- **Memory-intensive**: Schedule to NUMA nodes with local memory access
- **Distributed training**: Coordinate GPU + NIC on same PCIe fabric

**Best Practices:**

- Use DRA for complex device requirements (GPU + NIC + storage)
- Configure Topology Manager policy: `single-numa-node` for latency-sensitive
  workloads
- Label nodes with topology information: `topology.kubernetes.io/zone`,
  `gpu-interconnect=nvlink`
- Use Kueue or Volcano for rack-level topology awareness
- Test topology impact: benchmark with and without alignment
- Consider trade-offs: topology optimization may reduce scheduling flexibility

**Related Blog Post:**
[Topology-Aware Scheduling Blog](../blog/2025-11-25/topology-aware-scheduling.md)
for detailed coverage of DRA topology management.

### 2.7 Borrow & LendingLimit

**Concept**: Allow namespaces/teams to borrow unused resources from other
teams while enforcing lending limits to ensure fair access.

**Resource Borrowing Models:**

- **Elastic quotas**: Namespace can use more than guaranteed if available
- **Cohort-based sharing**: Teams in same cohort can borrow from each other
- **Time-based lending**: Borrow idle resources during off-peak hours

**Parameters:**

- **Guaranteed quota**: Minimum resources always available
- **Max quota**: Maximum resources including borrowed capacity
- **Lending limit**: Maximum resources that can be lent to others
- **Reclaim policy**: How to reclaim borrowed resources (preemption, graceful)

**Implementation:**

- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>: Cohorts and
  borrowing limits with preemption
- <a href="https://github.com/koordinator-sh/koordinator">`Koordinator`</a>:
  Elastic quota management

**Example (Kueue ClusterQueue):**

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: team-a-queue
spec:
  namespaceSelector: {}
  resourceGroups:
  - coveredResources: ["cpu", "memory", "nvidia.com/gpu"]
    flavors:
    - name: default-flavor
      resources:
      - name: "cpu"
        nominalQuota: 100      # Guaranteed
        borrowingLimit: 50     # Can borrow up to 50 more
        lendingLimit: 30       # Can lend up to 30
      - name: "nvidia.com/gpu"
        nominalQuota: 10
        borrowingLimit: 5
        lendingLimit: 3
```

**Best Practices:**

- Set lending limits to prevent resource starvation (e.g., lend max 30% of
  guaranteed)
- Use preemption to reclaim borrowed resources when owner needs them
- Monitor borrowing patterns and adjust quotas based on actual usage
- Combine with priority classes: borrowed workloads at lower priority

### 2.8 Descheduler

**Concept**: Continuously rebalance pods across nodes to optimize utilization,
correct scheduling mistakes, and adapt to changing conditions.

**Descheduling Strategies:**

- **RemoveDuplicates**: Ensure one pod per ReplicaSet on each node
- **LowNodeUtilization**: Move pods from underutilized to overutilized nodes
- **RemovePodsViolatingNodeAffinity**: Fix affinity violations
- **RemovePodsViolatingInterPodAntiAffinity**: Fix anti-affinity violations
- **RemovePodsViolatingTopologySpreadConstraint**: Rebalance topology spread
- **RemoveFailedPods**: Clean up failed pods
- **RemovePodsHavingTooManyRestarts**: Remove crashlooping pods

**Implementation:**

- <a href="https://github.com/kubernetes-sigs/descheduler">`Descheduler`</a>:
  Kubernetes SIG Project for pod eviction
- <a href="https://github.com/koordinator-sh/koordinator">`Koordinator`</a>:
  Built-in descheduling with load-aware rebalancing

**Example Configuration:**

```yaml
apiVersion: descheduler/v1alpha2
kind: DeschedulerPolicy
profiles:
- name: default
  pluginConfig:
  - name: LowNodeUtilization
    args:
      thresholds:
        cpu: 20
        memory: 20
      targetThresholds:
        cpu: 50
        memory: 50
  - name: RemovePodsViolatingTopologySpreadConstraint
    args:
      constraints:
      - topologyKey: topology.kubernetes.io/zone
```

**Best Practices:**

- Run descheduler periodically (every 10-30 minutes) not continuously
- Set pod disruption budgets (PDBs) to limit eviction impact
- Exclude critical pods using namespace/label selectors
- Monitor descheduling impact on application SLAs
- Use dry-run mode to preview evictions before applying

### 2.9 SLA-Based Scheduling

**Concept**: Schedule pods based on Service Level Agreement (SLA) requirements
using numeric thresholds, enabling workload placement on nodes meeting specific
reliability and performance criteria.

Kubernetes is introducing native SLA-based scheduling capabilities through
[KEP-5471: Extended Toleration Operators for Threshold-Based
Placement](https://github.com/kubernetes/enhancements/pull/5473). This
enhancement enables pods to express SLA requirements using numeric comparisons
in tolerations, providing a Kubernetes-native mechanism for SLA-aware
scheduling.

**Key Capabilities:**

- **Numeric Comparison Operators**: Extends tolerations to support `Lt`
  (less than) and `Gt` (greater than) operators for matching node taints with
  numeric values
- **SLA Threshold-Based Placement**: Allows pods to specify minimum SLA
  requirements (e.g., "only schedule on nodes with SLA > 95%")
- **Eviction Support**: Combines with `NoExecute` taint effect to automatically
  evict pods when node SLA drops below threshold
- **Feature Gate**: `TaintTolerationComparisonOperators` (alpha in Kubernetes
  v1.35)

**Use Cases:**

For large-scale deployments, SLA-based scheduling provides fine-grained
control over workload placement:

- **Critical workloads**: Require high-SLA nodes (>95%) to minimize latency and
  ensure consistent performance
- **Best-effort workloads**: Tolerate lower-SLA nodes for cost optimization
  while maintaining acceptable performance
- **Heterogeneous clusters**: Enable mixing on-demand (high-SLA) and spot
  (low-SLA) nodes with automatic workload steering based on reliability
  requirements
- **AI/ML workloads**: Prefill phases can require high-SLA nodes for TTFT
  optimization, while decode phases may tolerate lower-SLA nodes

**Example Configuration:**

```yaml
# High-SLA on-demand node with 95% SLA taint
apiVersion: v1
kind: Node
metadata:
  name: ondemand-gpu-node-1
spec:
  taints:
  - key: node.kubernetes.io/sla
    value: "950"  # 95.0% SLA (scaled by 10)
    effect: NoExecute
---
# Critical pod requires SLA > 95% with eviction support
apiVersion: v1
kind: Pod
metadata:
  name: critical-worker
spec:
  tolerations:
  - key: node.kubernetes.io/sla
    operator: Gt
    value: "950"
    effect: NoExecute
    tolerationSeconds: 30  # Grace period before eviction
  containers:
  - name: app
    image: critical-app:latest
---
# Best-effort pod tolerates lower SLA for cost savings
apiVersion: v1
kind: Pod
metadata:
  name: batch-worker
spec:
  tolerations:
  - key: node.kubernetes.io/sla
    operator: Gt
    value: "800"  # 80% SLA acceptable
    effect: NoExecute
    tolerationSeconds: 60
  containers:
  - name: batch
    image: batch-app:latest
```

**Integration with Other Strategies:**

SLA-based scheduling complements other optimization strategies:

1. **Runtime Placement Control**: Ensures workloads are placed on nodes meeting
   their reliability requirements
2. **Dynamic Adaptation**: Taints with `NoExecute` effect trigger automatic
   pod eviction when node SLA degrades, enabling graceful failover
3. **Cost Optimization**: Balance performance requirements with infrastructure
   costs by placing workloads on appropriate SLA tiers
4. **Topology Awareness**: Combine with topology-aware scheduling for both
   physical placement and SLA requirements

**Best Practices:**

- Use consistent SLA value scaling (e.g., multiply by 10 for percentages)
- Set appropriate `tolerationSeconds` based on workload criticality
- Monitor node SLA metrics and update taints dynamically
- Combine with PriorityClasses for comprehensive workload management
- Use preemption policies to ensure critical workloads get high-SLA nodes
- Test SLA thresholds under load to validate proper workload distribution

---

## Learning Topics

- **Scheduler architecture**: Queue, cache, framework, plugins
- **Scheduling algorithms**: Binpack, spread, load-aware, topology-aware,
  SLA-based
- **Multi-tenancy**: Resource quotas, priorities, fair sharing
- **Scheduling metrics**: Throughput, latency, utilization, queue depth
- **Conflict resolution**: Optimistic concurrency, retries, backoff

## Projects and Resources

**Schedulers:**

- <a href="https://github.com/kubernetes/kubernetes">`Kubernetes Default
  Scheduler`</a>: Extensible via scheduling framework
- <a href="https://github.com/volcano-sh/volcano">`Volcano`</a>: CNCF
  Incubating, batch scheduling
- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>: Kubernetes
  SIG Project, job queuing
- <a href="https://github.com/koordinator-sh/koordinator">`Koordinator`</a>:
  CNCF Sandbox, QoS and colocation
- <a href="https://github.com/kubewharf/godel-scheduler">`Godel
  Scheduler`</a>: ByteDance, high-throughput scheduling
- <a href="https://github.com/apache/yunikorn-core">`Apache YuniKorn`</a>:
  Apache, DRF and multi-tenancy
- <a href="https://github.com/NVIDIA/kai-scheduler">`NVIDIA Kai
  Scheduler`</a>: NVIDIA, GPU-optimized scheduling
- <a href="https://github.com/NVIDIA/grove">`NVIDIA Grove`</a>: Gang
  scheduling for AI workloads

**Device Management:**

- <a href="https://github.com/kubernetes/dynamic-resource-allocation/">`DRA`</a>:
  Dynamic Resource Allocation for Kubernetes
- <a href="https://github.com/containerd/nri">`NRI`</a>: Node Resource
  Interface for containerd
- <a href="https://github.com/Project-HAMi/HAMi">`HAMI`</a>: CNCF Sandbox,
  GPU sharing

**Monitoring:**

- <a href="https://github.com/kubernetes-sigs/scheduler-plugins">`Scheduler
  Plugins`</a>: Out-of-tree scheduler plugins
- <a href="https://github.com/kubernetes-sigs/descheduler">`Descheduler`</a>:
  Kubernetes SIG Project

**Documentation:**

- [Kubernetes Scheduling
  Framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)
- [Priority and
  Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/)
- [Dynamic Resource Allocation
  (DRA)](./dra.md)

## RoadMap (Ongoing Proposals)

- Gang Scheduling Support in Kubernetes
  [#4671](https://github.com/kubernetes/enhancements/pull/4671)
- LWS Gang Scheduling
  [KEP-407](https://github.com/kubernetes-sigs/lws/blob/main/keps/407-gang-scheduling/README.md)
- DRA: Structured Parameters
  [#4381](https://github.com/kubernetes/enhancements/issues/4381) (GA in
  v1.34)
- SLA-Based Scheduling: Extended Toleration Operators
  [KEP-5471](https://github.com/kubernetes/enhancements/pull/5473) (Alpha in
  v1.35)

## Best Practices Summary

1. **Start with observability**: Measure current scheduling performance and
   utilization before optimizing
2. **Optimize incrementally**: Address biggest bottlenecks first (API, etcd,
   admission webhooks)
3. **Balance throughput vs. utilization**: High concurrency improves
   throughput but may reduce utilization
4. **Use appropriate tools**: Match scheduler to workload (batch, serving,
   training)
5. **Monitor continuously**: Track scheduling latency, queue depth,
   utilization, conflicts
6. **Test at scale**: Validate optimizations with realistic workload patterns
   and cluster sizes

---

## Avoiding Scheduling Overhead

In some cases, the best optimization is to avoid scheduling entirely by
updating pods in-place rather than recreating them. This eliminates both
scheduling latency and pod startup time.

### Vertical Pod Autoscaler (VPA)

**Concept**: Automatically adjust CPU and memory requests/limits for running
pods without restarting them (when using in-place resize).

**In-Place Pod Resize (KEP-1287):**

Kubernetes v1.27+ supports in-place resizing of pod resource requests and
limits without pod restart, enabled by the `InPlacePodVerticalScaling` feature
gate.

**Benefits:**

- **No scheduling overhead**: Pod remains on same node, no scheduler
  involvement
- **No startup time**: Container continues running with adjusted resources
- **Minimal disruption**: Especially for stateful workloads with long startup
  times
- **Faster scaling**: Resource adjustments apply in seconds vs. minutes for
  pod recreation

**Example Usage:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: inference-worker
spec:
  containers:
  - name: model-server
    image: inference-engine:latest
    resources:
      requests:
        memory: "4Gi"
        cpu: "2"
      limits:
        memory: "8Gi"
        cpu: "4"
    resizePolicy:
    - resourceName: cpu
      restartPolicy: NotRequired  # Resize without restart
    - resourceName: memory
      restartPolicy: RestartContainer  # May restart if needed
```

**VPA Configuration for In-Place Updates:**

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: inference-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inference-deployment
  updatePolicy:
    updateMode: "Auto"  # Automatically apply recommendations
  resourcePolicy:
    containerPolicies:
    - containerName: model-server
      mode: Auto
      minAllowed:
        cpu: "1"
        memory: "2Gi"
      maxAllowed:
        cpu: "8"
        memory: "16Gi"
```

**Best Practices:**

- Test in-place resize with your workloads (some apps don't handle resource
  changes gracefully)
- Set appropriate min/max limits to prevent over-provisioning
- Monitor resource utilization to validate VPA recommendations
- Use `NotRequired` restart policy for CPU (usually safe), evaluate for memory
- Combine with HPA for comprehensive autoscaling (scale pods + resize)

### Container/Pod In-Place Restart

**Concept**: Restart containers within a pod without recreating the pod or
rescheduling, useful for recovering from failures or applying certain
configuration changes while preserving pod placement and identity.

**Kubernetes KEPs:**

- **KEP-5307: Container Restart Policy**: Provides fine-grained control over
  individual container restart behavior within pods
- **KEP-5532: Restart All Containers on Container Exits**: Enables restarting
  all containers in a pod when specific containers exit, useful for
  coordinated restarts

**Use Cases:**

- **Crash recovery**: Automatically restart failed containers without pod
  rescheduling
- **Coordinated restarts**: Restart all containers together when dependencies
  fail
- **Container-level policies**: Apply different restart behaviors to sidecar
  vs. main containers
- **Debug/troubleshooting**: Faster recovery without scheduling overhead

**Container Restart Rules:**

Kubernetes supports configuring restart behavior at the container level:

- **Container restart policy**: Control whether individual containers restart
  on failure
- **Pod restart policy**: `Always`, `OnFailure`, `Never` still apply at pod
  level
- **Coordinated restarts**: KEP-5532 enables restarting all containers when
  specific ones exit

**Benefits:**

- **No scheduling overhead**: Container restarts on same node, no scheduler
  involvement
- **Preserves pod identity**: Pod IP, hostname, and volumes remain unchanged
- **Faster recovery**: Container restart is faster than full pod recreation
- **Fine-grained control**: Different restart policies per container within pod

#### Real-World Use Case: JobSet In-Place Restart

<a href="https://github.com/kubernetes-sigs/jobset/">JobSet</a> is implementing
in-place restart functionality that demonstrates the significant performance
benefits of avoiding pod recreation and rescheduling. According to a [benchmark
prototype](https://github.com/kubernetes-sigs/jobset/compare/main...GiuseppeTT:jobset:in-place-restart-prototype),
in-place restart achieved:

- **Restart time reduction**: From 2m10s to 10s (92% faster)
- **Test scale**: 5000 nodes cluster
- **Benefit**: Dramatically faster recovery for distributed batch workloads

This demonstrates how in-place restart is particularly valuable for:

- **Large-scale batch jobs**: Where coordinating thousands of pods without
  rescheduling saves significant time
- **Distributed training**: Quick recovery from failures without losing cluster
  placement
- **Job dependencies**: Restarting related jobs together while maintaining
  pod identity and network connectivity

More details in the [JobSet in-place restart design
document](https://docs.google.com/document/d/16zexVooHKPc80F4dVtUjDYK9DOpkVPRNfSv0zRtfFpk/edit?tab=t.0#heading=h.y6xl7juq7465).

**Example - Pod with Container Restart Policies:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-app
spec:
  restartPolicy: Always  # Pod-level policy
  containers:
  - name: main-app
    image: app:latest
    # Container will restart based on pod-level policy
  - name: sidecar
    image: sidecar:latest
    # KEP-5307: Future support for container-level restart policy
```

**Trade-offs:**

- **Pro**: Eliminates scheduling latency, faster recovery
- **Con**: Node-local resource constraints may require pod rescheduling if
  resources exhausted
- **Pro**: Preserves pod IP and network identity
- **Con**: Doesn't rebalance load across cluster

**When to Use:**

- Stateful workloads with long startup times (databases, caches)
- GPU workloads with expensive model loading
- Multi-container pods with sidecar dependencies
- Fast failure recovery without disrupting pod placement

**References:**

- [KEP-5307: Container Restart
  Policy](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5307-container-restart-policy/README.md)
- [KEP-5532: Restart All Containers on Container
  Exits](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/5532-restart-all-containers-on-container-exits/README.md)

---

*Some content generated with AI assistance. Please verify for your specific
use case.*
