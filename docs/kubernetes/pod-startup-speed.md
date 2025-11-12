---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: kubernetes, pod, startup, optimization, performance
canonical_path: docs/kubernetes/pod-startup-speed.md
---

# Pod Startup Speed Optimization

This guide provides comprehensive strategies to accelerate Pod startup in
Kubernetes clusters, particularly for large-scale deployments and AI/GPU
workloads. Based on KubeCon 2023 China presentation by Paco Xu (DaoCloud) and
Byron Wang (Birentech).

## Why Pod Startup Speed Matters

Fast Pod startup is critical for:

- **Rapid scaling**: Responding quickly to load increases
- **Efficient resource utilization**: Minimizing idle time
- **Better user experience**: Reducing wait times for services
- **Cost optimization**: Faster iteration and deployment cycles
- **AI/GPU workloads**: Quick model loading and inference startup

## Typical Pod Startup Times

Pod startup time varies based on complexity:

- **< 50ms**: Minimal pods with local images
- **~ 100ms**: Simple pods with cached images
- **~ seconds**: Standard applications with moderate initialization
- **15s - 1m**: Applications with significant initialization or large images
- **< 5m**: Complex applications with extensive data loading

## Pod Startup Pipeline

Pod startup involves four main phases:

1. **Pod Creation**: API Server processes the Pod creation request
2. **Pod Scheduling**: Scheduler assigns the Pod to a node
3. **Pod Startup on Node**: Kubelet creates and starts containers
4. **Observability**: Monitoring and measuring startup performance

---

## 1. Pod Creation Optimization

### API Server Performance

**Common Issues:**

- Slow etcd performance
- High API Server load
- Rate limits being hit
- Slow admission webhooks

**Solutions:**

- Monitor and optimize etcd performance
- Scale API Server horizontally for high load
- Review and optimize admission webhook performance
- Tune rate limits appropriately for workload

### Pod Creation Failures

**Common Causes:**

- **Validation failures**: Invalid Pod specifications
- **Pod Security Admissions**: Security policies blocking Pod creation
- **Resource quotas**: Namespace resource limits reached
- **Pod Priority and Preemption**: Lower priority Pods waiting for resources

**Solutions:**

- Validate Pod specs before submission
- Review and adjust Pod Security policies
- Monitor namespace resource quotas
- Use appropriate Pod priority classes

---

## 2. Pod Scheduling Optimization

### Default Scheduler

The scheduler must find an appropriate node if `pod.spec.nodeName` is not
specified.

**Factors Affecting Scheduling:**

- **Failures/Retry**: Pod scheduling failures and retry logic
- **Scale**: Number of nodes in the cluster
- **Conditions**: Node affinity, taints, tolerations
- **Load**: Number of Pods being scheduled simultaneously

### Advanced Scheduling Strategies

#### Load-Aware Scheduling

- **Trimaran**: Node-aware scheduling plugin
- Pods start on the least loaded nodes
- Reduces resource contention

#### Spread Strategy

- Distribute Pods across multiple nodes
- Reduces mutual interference during Pod startup
- Better resource distribution

### GPU Scheduling

For AI/GPU workloads, specialized scheduling algorithms are needed:

**GPU Scheduler Algorithms:**

- **Gang Scheduling**: Schedule all Pods in a group together or not at all
- **SKU-aware**: Consider GPU SKU/type in scheduling decisions
- **Binpack**: Maximize GPU utilization on fewer nodes
- **DRF (Dominant Resource Fairness)**: Fair resource allocation across users

**GPU Scheduling Challenges:**

1. Device number or property changes
2. Different device types from single vendor
3. Multiple vendors' devices in one cluster
4. Allocating a device to multiple Pods or containers
5. Allocating a specific selected device

**Solutions:**

- Custom Resource Definitions for GPUs (e.g., `birentech.com/gpu`)
- Dynamic Resource Allocation (DRA)
- GPU-aware schedulers (HAMI, NVIDIA Kai Scheduler, Grove)

---

## 3. Pod Startup on Node Optimization

### Simplified Pod Startup Steps

Basic Pod startup process:

1. Pull image
2. Sandbox creation
3. CNI (network initialization)
4. Volume mount or Secret/ConfigMap
5. Container main process starts

**Simplification strategies:**

- Pull images in advance
- Use `hostNetwork: true` when appropriate
- Minimize volume mounts
- Avoid CPU/memory limitations for startup-critical Pods

### Image Optimization

#### Make Images Smaller

**Best Practices:**

- Add `.dockerignore` to exclude unnecessary files
- Choose smaller base images: `alpine`, `scratch`
- Use multistage builds to exclude build-time dependencies
- Reduce layers: merge layers or use squash
- Don't install debug tools: use `kubectl debug` with ephemeral containers

**Tool:**

- <a href="https://github.com/wagoodman/dive">`wagoodman/dive`</a>: Tool
  for exploring each layer in a Docker image

#### P2P and Lazy Pulling

**Image Distribution Solutions:**

- <a href="https://github.com/dragonflyoss/dragonfly2">`Dragonfly`</a>:
  Open source P2P-based file distribution and image acceleration system
- <a href="https://github.com/dragonflyoss/nydus">`Nydus`</a>: Dragonfly
  Container Image Service for lazy pulling
- <a href="https://github.com/spegel-org/spegel">`Spegel`</a>: Stateless
  cluster local OCI registry mirror (lightweight)
- <a href="https://github.com/uber/kraken">`uber/kraken`</a>: P2P Docker
  registry capable of distributing TBs of data in seconds

**Containerd Integration:**

- <a href="https://github.com/containerd/stargz-snapshotter">`containerd/stargz-snapshotter`</a>:
  Lazy-pulling using Nydus Snapshotter

#### Parallel Image Pulling

By default, kubelet sends only one image pull request at a time.

**Configuration:**

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
serializeImagePulls: false
maxParallelImagePulls: 5  # Available since v1.27
```

**Why is `serializeImagePulls` true by default?**

- Old issue with aufs before Docker v1.9
- Performance issues before containerd 1.6.3 & 1.7.0
- Feedback welcome in
  <a href="https://github.com/kubernetes/kubernetes/issues/108405">#108405</a>

### Init Containers Optimization

**Best Practices:**

- Do only necessary initialization
- Run init containers in parallel when possible
- Use `postStart` hook if appropriate
- Make preparations as early as possible:
  - Can this be done during image building?
  - Can this be done with a DaemonSet/Pod on node?

### CPU Management

#### Avoid CPU Throttling at Startup

**Strategy:**

- Use larger CPU limits at the beginning
- Avoid CPU throttling during initialization

**Better Solution (v1.27+):**

- Use Vertical Pod Autoscaler (VPA) with In-Place Pod Vertical Scaling:

```bash
--feature-gates=InPlacePodVerticalScaling=true
```

#### Static CPU Policy

For guaranteed QoS Pods requiring dedicated CPU cores:

**Steps to Change CPU Manager Policy:**

1. Drain the node
2. Stop kubelet
3. Remove old CPU manager state file:
   `/var/lib/kubelet/cpu_manager_state`
4. Edit kubelet configuration to set desired CPU manager policy
5. Start kubelet

**⚠️ Limitation:**

- See <a href="https://github.com/kubernetes/kubernetes/issues/116086">#116086</a>
- If your Pod has sidecar containers, the sidecar CPU limit/request must be
  `Guaranteed`

### Probe Configuration

**Startup Probe:**

- If set, decrease readiness probe's `initialDelaySeconds`
- Protects slow-starting containers

**Readiness Probe:**

- Set `initialDelaySeconds` if no startup probe is configured
- Prevents premature traffic routing

**Future Roadmap:**

- Sub-second/more granular probes: millisecond precision
- Reference: <a href="https://www.padok.fr/en/blog/kubernetes-probes">Kubernetes
  Probes Guide</a>

### Forensic Container Checkpointing

For Pods with slow startup due to:

- Loading extensive data into memory
- Time-consuming initialization processes

**Solution: Forensic Container Checkpointing** (Alpha in v1.25)

**How it works:**

1. Create a snapshot of the fully initialized Pod
2. Store snapshot for rapid reuse
3. Restore from checkpoint on subsequent starts

**Benefits:**

- Instantaneous response to user requests
- Efficient resource utilization
- Consistent performance across restarts

### gVisor Snapshots for AI Agents

For AI agent workloads requiring both fast startup and strong isolation:

**Solution: gVisor with Container Snapshots** (Production on GKE)

**How it works:**

1. Initialize container with dependencies, libraries, and runtime state
2. Create gVisor sandbox snapshot of pre-warmed container
3. Restore new instances from snapshot in milliseconds
4. Each instance runs in isolated gVisor sandbox

**Performance Impact:**

- **Up to 90% improvement** in cold start time compared to traditional
  containers
- Sub-second startup for complex agent workloads
- Eliminates initialization overhead for repeated agent invocations

**Use Cases:**

- **LLM Agents**: Fast execution of LLM-generated code in secure sandboxes
- **Function Calling**: Rapid invocation of agent functions with isolation
- **Serverless AI**: Near-instant cold starts for serverless agent platforms
- **Multi-Tenant AI**: Secure, fast startup for customer agent workloads

**Availability:**

- Production-ready in <a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
  GKE Agent Sandbox</a>
- Combines gVisor security with snapshot performance
- See [Workload Isolation Guide](./isolation.md#6-agent-sandbox-kubernetes-sig-project)
  for detailed security architecture

### General Factors

**Container Runtime:**

- Prefer containerd over Docker for better performance
- containerd is the default runtime in modern Kubernetes

**CNI Performance:**

- Most IPAM on node is very fast
- Choose appropriate CNI plugin for workload

**SELinux Optimization (v1.27+):**

- SELinux Relabeling with Mount Options (beta)
- Mounts volumes with correct SELinux label instead of recursive file changes
- Significantly faster for large volumes

**Kubelet Performance (v1.27+):**

- Default API QPS limits bumped 10x
- Event-triggered updates to container status (Evented PLEG is beta)

---

## 4. AI/GPU Specific Optimizations

### Dynamic Resource Allocation (DRA)

DRA provides flexible GPU resource management:

**Capabilities:**

1. Multiple resource arguments
2. Network-attached resources
3. Init and cleanup strategies
4. User-friendly API
5. Cluster add-ons for resource management
6. Complex allocation rules

**Caveats:**

1. Potentially slower Pod scheduling
2. Additional complexity in describing Pod requirements

### GPU Management Approaches

**Four Main Approaches:**

1. **New container runtime**: Custom runtime with GPU support
2. **CRI proxy**: Intercept CRI calls to add GPU functionality
3. **Modify kubelet core code**: Direct kubelet modifications
4. **DRA and CDI**: Use Dynamic Resource Allocation with Container Device
   Interface

### Speed Up Data Loading for AI/GPU

**Typical Data Loading Pipeline:**

1. **Prepare**: Stage data in storage
2. **Copy to memory**: Load data from storage to host memory
3. **Copy to GPU memory**: Transfer data from host to GPU memory
4. **GPU Compute**: Execute computation

**Optimization Strategies:**

- Pre-load data on nodes
- Use fast storage (NVMe, local SSDs)
- Optimize data transfer pipelines
- Consider GPU Direct Storage for direct GPU access

### Fake Device and Custom Scheduler

For testing and development:

- Use fake devices to simulate GPU environments
- Implement custom schedulers for specialized requirements
- Test scaling and performance without real hardware

---

## 5. Observability

### Metrics

**Key Metric (v1.26+):**

```text
pod_start_sli_duration_seconds
```

**Sample Log:**

```text
"Observed pod startup duration"
pod="kube-system/konnectivity-agent-gnc9k"
podStartSLOduration=-9.223372029479458e+09
pod.CreationTimestamp="2022-12-30 15:33:06"
firstStartedPulling="2022-12-30 15:33:09"
lastFinishedPulling="0001-01-01 00:00:00"
observedRunningTime="2022-12-30 15:33:13"
watchObservedRunningTime="2022-12-30 15:33:13"
```

**Use Cases:**

- Create alerts based on this metric
- Monitor Pod startup SLO compliance
- Identify slow-starting Pods
- Track startup time trends

### Linux Tools for Debugging

Use standard Linux performance tools:

- `top`, `htop`: CPU and memory usage
- `iostat`: I/O statistics
- `perf`: Performance profiling
- `strace`: System call tracing
- `tcpdump`: Network packet analysis
- `bpftrace`, `bcc`: eBPF-based tracing

---

## Summary

Pod startup optimization is a multi-faceted challenge requiring attention to:

1. **API Server and etcd performance**
2. **Scheduler efficiency and placement decisions**
3. **Image size and distribution strategy**
4. **Container runtime and CNI performance**
5. **Resource allocation and CPU management**
6. **AI/GPU specific considerations**
7. **Snapshots and checkpointing** for pre-warmed containers
8. **Comprehensive observability**

By applying these strategies systematically, you can significantly reduce Pod
startup times and improve overall cluster performance. For AI agent workloads,
gVisor snapshots in GKE Agent Sandbox can provide up to 90% improvement in
cold start performance while maintaining strong isolation guarantees.

---

## References

- KubeCon 2023 China: "How Can Pod Start-up Be Accelerated on Nodes in Large
  Clusters?" by Paco Xu (DaoCloud) and Byron Wang (Birentech)
- <a href="https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/">Pod
  Lifecycle Official Documentation</a>
- <a href="https://github.com/kubernetes/kubernetes/issues/108405">Kubernetes
  Issue #108405: Serial Image Pulls</a>
- <a href="https://github.com/kubernetes/kubernetes/issues/116086">Kubernetes
  Issue #116086: CPU Manager Limitations</a>
- <a href="https://www.padok.fr/en/blog/kubernetes-probes">Kubernetes Probes
  Guide</a>
- <a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
  GKE Agent Sandbox: Strong Guardrails for Agentic AI on Kubernetes</a>
