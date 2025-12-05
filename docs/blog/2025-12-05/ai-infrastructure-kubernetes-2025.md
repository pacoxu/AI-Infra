---
status: Active
maintainer: pacoxu
date: 2025-12-05
tags: kubernetes, ai-infrastructure, gpu, large-scale, multi-cluster, survey
canonical_path: docs/blog/2025-12-05/ai-infrastructure-kubernetes-2025.md
source: https://kube.today/ai-infrastructure-2025
---

# AI Infrastructure on Kubernetes: 2025 Survey Insights and Best Practices

As AI workloads increasingly move to Kubernetes, understanding the real-world
challenges and deployment patterns becomes critical. This article explores key
insights from recent surveys and industry observations about running AI
infrastructure at scale on Kubernetes.

## Key Survey Findings

Recent surveys of Kubernetes practitioners running AI workloads reveal
surprising insights about the current state of AI infrastructure:

### Large-Scale Cluster Reality Check

**Only 12% of respondents have actually experienced 10,000+ node clusters in
production environments.** This statistic highlights an important gap between
industry hype and practical reality:

- Most organizations operate at much smaller scales (100-1000 nodes)
- The challenges discussed in "hyperscale" talks may not apply to majority
- Focus should be on practical optimizations for typical cluster sizes
- Lessons from large-scale deployments still provide valuable insights

### GPU Utilization Challenges

GPU utilization remains one of the most critical challenges in AI
infrastructure:

**Common Utilization Patterns:**

- **Development/Testing**: 10-30% GPU utilization
- **Training workloads**: 40-70% GPU utilization
- **Inference workloads**: 20-50% GPU utilization
- **Best-in-class**: 70-85% GPU utilization

**Key Challenges Identified:**

1. **Resource Fragmentation**
   - Pods requesting full GPUs but using only a fraction
   - Lack of GPU sharing and time-slicing adoption
   - Poor bin-packing due to topology constraints

2. **Idle Time Between Jobs**
   - Job queue delays and scheduling latency
   - Slow image pulls and pod startup times
   - Manual intervention requirements

3. **Development Inefficiencies**
   - Interactive notebooks holding GPUs idle
   - Long debug cycles with GPUs allocated
   - Lack of preemption for lower-priority work

**Improvement Strategies:**

- Implement GPU sharing (MIG, time-slicing, vGPU)
- Use spot/preemptible instances for training
- Adopt dynamic resource allocation (DRA)
- Implement GPU pooling and fractional allocation
- Enable automatic scale-down during idle periods

### Training and Inference Workload Separation

**Why Separation Matters:**

The survey highlights growing adoption of **training-inference workload
separation** as a best practice:

**Training Characteristics:**

- Batch processing with high GPU utilization bursts
- Long-running jobs (hours to weeks)
- Fault-tolerant with checkpointing
- Requires gang scheduling and multi-node coordination
- Network-intensive (all-reduce, collective operations)

**Inference Characteristics:**

- Real-time serving with strict latency SLOs
- Continuous operation (24/7)
- Requires high availability and auto-scaling
- Focus on throughput and cost per query
- Can leverage model caching and batching

**Benefits of Separation:**

1. **Resource Optimization**
   - Training clusters: Optimize for throughput and cost
   - Inference clusters: Optimize for latency and availability
   - Different GPU types per workload (A100 for training, T4 for inference)

2. **Operational Efficiency**
   - Independent scaling policies
   - Separate upgrade windows
   - Isolated failure domains
   - Different monitoring and alerting strategies

3. **Cost Management**
   - Spot instances for training (70% cost savings)
   - Reserved instances for inference (predictable costs)
   - Rightsizing per workload type

**Implementation Patterns:**

```yaml
# Training Cluster Profile
- Node pools: GPU-optimized with NVLink/InfiniBand
- Schedulers: Kueue, Volcano with gang scheduling
- Storage: High-bandwidth shared filesystems
- Networking: RDMA-enabled for distributed training
- Workloads: Kubeflow, PyTorch Elastic, DeepSpeed

# Inference Cluster Profile
- Node pools: Mixed GPU/CPU with autoscaling
- Serving: KServe, Seldon, vLLM, TensorRT
- Storage: Model registry with fast local caching
- Networking: Service mesh with traffic shaping
- Workloads: REST APIs, gRPC endpoints
```

## AI Infrastructure Architecture Patterns

### Single Cluster vs Multi-Cluster Deployment

**Single Cluster Approach:**

- Simpler operations and unified management
- Shared resource pool with better utilization
- Suitable for organizations under 500-1000 nodes
- Lower operational overhead

**Multi-Cluster Approach:**

- Environment isolation (dev/staging/prod)
- Geographic distribution for latency
- Regulatory compliance (data sovereignty)
- Blast radius limitation
- Suitable for larger organizations (1000+ nodes)

### Kubernetes for AI: Core Components

**Resource Management:**

- **Device Plugins**: GPU/NPU device discovery and allocation
- **DRA (Dynamic Resource Allocation)**: Next-gen flexible resource management
- **Node Feature Discovery**: Hardware capability detection
- **Topology Manager**: NUMA and device topology awareness

**Scheduling:**

- **Default Scheduler** with score plugins
- **Kueue**: Multi-tenant job queueing
- **Volcano**: Batch scheduling with gang scheduling
- **Karpenter**: Just-in-time node provisioning

**Workload Management:**

- **Job/CronJob**: Single training runs
- **JobSet**: Multi-job coordination (alpha)
- **Kubeflow Training Operators**: Framework-specific (PyTorch, TensorFlow)
- **LeaderWorkerSet**: Distributed inference orchestration

**Storage:**

- **Persistent Volumes**: Model storage and checkpoints
- **CSI Drivers**: Cloud-native storage integration
- **Shared Filesystems**: Training data distribution (NFS, Lustre)
- **Object Storage**: Model artifacts and datasets (S3, GCS)

## Best Practices for AI on Kubernetes

### 1. Right-Size Your Infrastructure

**Don't over-engineer for hyperscale:**

- Start with appropriate cluster sizes (100-500 nodes)
- Scale horizontally with multiple clusters as needed
- Focus on GPU utilization over raw node count
- Monitor and optimize before expanding

### 2. Implement GPU Sharing

**Maximize GPU ROI:**

- Use MIG on A100/H100 for multi-tenant isolation
- Implement time-slicing for development workloads
- Consider fractional GPU allocation for inference
- Monitor per-pod GPU metrics

### 3. Optimize for Cost

**Training Cost Strategies:**

- Use spot/preemptible instances (60-90% savings)
- Implement automatic checkpointing
- Enable job preemption for priority scheduling
- Right-size instance types (don't always use largest GPUs)

**Inference Cost Strategies:**

- Use smaller GPU types (T4, L4) for appropriate models
- Implement dynamic batching
- Enable autoscaling based on request rate
- Consider CPU inference for smaller models

### 4. Monitoring and Observability

**Key Metrics to Track:**

- GPU utilization and memory usage per pod
- Job queue depth and scheduling latency
- Pod startup time and image pull duration
- Training throughput (samples/second)
- Inference latency (p50, p95, p99)
- Cost per training run and per inference query

**Tools:**

- **DCGM Exporter**: NVIDIA GPU metrics
- **Prometheus + Grafana**: Metrics collection and visualization
- **Kubeflow Pipelines**: ML workflow tracking
- **MLflow/Weights & Biases**: Experiment tracking

### 5. Network Optimization

**Training:**

- Enable RDMA for distributed training
- Use topology-aware scheduling (GPU + NIC affinity)
- Implement network policies for security
- Monitor cross-node bandwidth

**Inference:**

- Use service mesh for traffic management (Istio, Linkerd)
- Implement connection pooling
- Enable HTTP/2 and gRPC
- Consider edge caching for model serving

## Common Pitfalls to Avoid

1. **Over-provisioning GPUs**: Requesting full GPUs when fractions suffice
2. **Ignoring Pod Startup Time**: Not optimizing image size and pull strategies
3. **Manual Job Management**: Not using job queue systems (Kueue, Volcano)
4. **Single Point of Failure**: Not implementing HA for critical services
5. **Neglecting Cost Monitoring**: Running expensive GPU nodes 24/7 without usage
6. **Poor Resource Limits**: Not setting requests/limits leading to node
   instability
7. **Inadequate Checkpointing**: Losing hours of training on spot interruptions
8. **Monolithic Clusters**: Mixing all workload types without isolation

## Looking Ahead: Future Trends

### Emerging Technologies

- **DRA GA**: Dynamic Resource Allocation graduating to stable
- **JobSet**: Multi-job orchestration for complex training
- **In-Place Pod Resize**: Adjust resources without restart
- **Topology-Aware Scheduling**: Better GPU/NIC placement
- **KEP-4817 Job Success/Completion Policies**: Better job lifecycle management

### Industry Direction

- Increased adoption of inference-specific clusters
- Growth in multi-cluster management tools
- Better GPU sharing and virtualization
- Simplified ML platform abstractions on Kubernetes
- Integration with serverless for hybrid workloads

## Conclusion

Running AI infrastructure on Kubernetes is maturing rapidly, but the survey
data shows a gap between aspirational hyperscale discussions and practical
deployments. Key takeaways:

1. **Most organizations operate well below 10K nodes** - optimize for your
   actual scale
2. **GPU utilization is the #1 challenge** - implement sharing and monitoring
3. **Separate training and inference** - different requirements need different
   strategies
4. **Cost optimization is critical** - use spot instances, right-size, and
   monitor
5. **Start simple, scale deliberately** - don't over-engineer from day one

The Kubernetes ecosystem continues to evolve with better AI-native features.
Stay focused on practical improvements that drive GPU utilization and cost
efficiency for your specific scale and requirements.

## Multi-Cluster Use Cases

Different organizations adopt multi-cluster strategies for various reasons.
Understanding these use cases helps inform architectural decisions:

<img src="../../../diagrams/multicluster-use-cases.png" alt="Multi-Cluster Use Cases" width="100%">

### Environment-Based Separation (Most Common)

**Development → Staging → Production**

Organizations deploy separate clusters for each environment to:

- Test deployment safely without breaking live systems
- Maintain production stability and uptime
- Enable experimentation in dev/staging
- Implement different security policies per environment

### Region-Based Deployment

**Cluster per Region for High Performance**

Geographic distribution provides:

- Lower latency for end users
- Geo-redundancy for disaster recovery
- Better service availability across regions
- Compliance with data residency requirements

### Business Unit Isolation

**Cluster per Business Unit for Team Ownership**

Separate clusters enable:

- Independent scaling and updates
- Team autonomy and ownership
- Easy compliance and auditing
- Budget allocation per team

### Isolation for Security and Management

**Workload Isolation**

Different isolation dimensions:

- Improved security posture
- Simplified management and access control
- Better blast radius limitation
- Easier troubleshooting and debugging

### Infrastructure Provider Flexibility

**Multi-Cloud or Hybrid Deployment**

Running clusters across providers:

- Single cloud, multiple regions
- Multi-cloud for vendor independence
- On-premises and edge locations
- Flexible deployment avoiding lock-in

These patterns often combine - organizations may use multiple strategies
simultaneously (e.g., multi-region with dev/staging/prod in each region).

## References

- Original article: <https://kube.today/ai-infrastructure-2025>
- [Kubernetes Large-Scale Clusters](../../kubernetes/large-scale-clusters.md)
- [GPU Scheduling and Management](../../kubernetes/scheduling-optimization.md)
- [Training on Kubernetes](../../training/README.md)
- [Inference Optimization](../../inference/README.md)

---

*This article synthesizes insights from industry surveys, KubeCon
presentations, and real-world AI infrastructure deployments on Kubernetes.*
