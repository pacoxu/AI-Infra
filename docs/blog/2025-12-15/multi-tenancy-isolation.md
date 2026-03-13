---
status: Active
maintainer: pacoxu
date: 2025-12-15
tags: kubernetes, multi-tenancy, isolation, security, ai-infra, public-cloud, private-cloud
canonical_path: docs/blog/2025-12-15/multi-tenancy-isolation.md
---

# Multi-Tenancy Isolation Solutions in the AI Infra Era

[中文版](./multi-tenancy-isolation_zh.md)

## Introduction

As AI infrastructure scales to support diverse workloads across training and inference, multi-tenancy isolation has
become a critical architectural concern. The requirements differ significantly between public cloud and private cloud
deployments, as well as between training and inference workloads. This document explores isolation strategies tailored
to these scenarios.

## Public Cloud vs Private Cloud: Training and Inference Considerations

The following table highlights key differences in how AI infrastructure is designed and operated across cloud types and
workload categories:

| Dimension / Scenario | Public Cloud · Training | Private Cloud · Training | Public Cloud · Inference | Private Cloud · Inference |
| --- | --- | --- | --- | --- |
| **Typical Use Cases** | Short-term large-scale pre-training, fine-tuning, hyperparameter search; ephemeral clusters | Long-term enterprise training; multi-team shared GPU pools | Public LLM APIs, AIGC services across regions | Internal Q&A, office assistants, knowledge bases, business system AI |
| **Resources & Elasticity** | High GPU elasticity; large-scale ephemeral clusters; heavy use of Spot/Preemptible instances | Fixed GPU pools; focus on scheduling and quotas; multi-vendor/multi-model coexistence | Auto-scaling by QPS/concurrency; multi-region deployment | Controlled scale; typically 1-2 data centers with multi-cluster multi-tenancy |
| **Cost Model** | OPEX-driven; focus on per-job total cost; leverage discounts and Spot instances | CapEx-driven; key goal is long-term GPU utilization ≥60-70% | Scale down replicas during low traffic, scale up during peaks; avoid idle GPUs | GPUs are fixed assets; use multi-tenancy, multi-model, and batch processing to maximize utilization |
| **Scheduling & Platform** | Kueue/Volcano/Ray for elastic and preemptible workloads; cloud-managed training services | Gang scheduling, priority, quota management; strong topology awareness (NVLink/RDMA/MIG/vGPU) | Cloud-managed gateways, load balancers, monitoring, managed inference platforms (Bedrock/Vertex/SageMaker) | Self-hosted KServe/vLLM/Ray Serve/Triton; integrated with existing gateways, monitoring, and audit systems |
| **Data & Storage** | Data in object storage; cross-AZ/Region bandwidth and traffic costs; frequent checkpoints to object storage | Data in enterprise data lakes / HDFS / Ceph / MinIO; data center-level topology awareness; training close to data | RAG indexes, vector DBs use managed storage; multi-region data replication | Self-hosted vector DBs (Milvus/Qdrant/pgvector); all data remains in internal networks |
| **SLO / Reliability** | Training tolerates preemption; focus on checkpointing + auto-recovery; accepts job interruptions and rescheduling | Long-running training; more emphasis on maintenance windows, migration, and rescheduling | P95/P99 latency, multi-region disaster recovery, canary deployments, A/B experiments | Low internal latency, high stability; unified with existing business SLOs (e.g., core transaction chains) |
| **Security & Compliance** | Cross-border/multi-region compliance (GDPR, etc.); heavy use of cloud KMS, WAF, audit services | Meet local regulations and enterprise internal standards; physical isolation + network segmentation | Public APIs require fraud detection, abuse prevention, data leak protection; rely on cloud security services | Full internal network; strict RBAC, auditing, data masking; typically no public internet access |
| **Key Challenges** | Competing for compute, quota limits; costs scale uncontrollably; architecture easily locked into cloud products | Multi-team GPU contention; balancing fairness and high utilization; complex hardware topology requiring deep scheduling customization | Global traffic routing, cross-region performance & costs; reliance on closed-source cloud capabilities | Self-assembled components, self-operated; balancing compliance, security, and compute utilization |

### Key Insights

**Public Cloud Training**:

- Optimized for burst workloads with elastic resources
- Spot instances reduce costs but require fault-tolerant designs
- Managed services simplify operations but may introduce vendor lock-in

**Private Cloud Training**:

- Focus on maximizing utilization of fixed GPU assets
- Multi-tenant scheduling with fairness and priority enforcement
- Strong topology awareness essential for RDMA, NVLink, and MIG

**Public Cloud Inference**:

- Auto-scaling and multi-region deployment for global user bases
- Managed inference platforms reduce operational overhead
- Cost control through dynamic replica scaling based on traffic patterns

**Private Cloud Inference**:

- Self-hosted solutions integrated with enterprise security and compliance frameworks
- Emphasis on internal network security and RBAC
- Model lifecycle management and multi-model serving to maximize GPU ROI

## Multi-Tenant Container Security Isolation Solutions in Kubernetes

Running mixed online/offline workloads in multi-tenant Kubernetes clusters requires layered isolation strategies.
Below are the primary approaches, ranging from strong to foundational isolation.

### 1. Strongest Isolation: Cluster / Control Plane Isolation

**Approach**: Separate Kubernetes clusters or control planes for untrusted tenants.

**Benefits**:

- Complete API server, etcd, and scheduler isolation
- Eliminates noisy neighbor issues at control plane level
- Simplifies security auditing and compliance

**Use Cases**:

- Mutually untrusted tenants (e.g., different enterprises in a public cloud)
- Regulatory requirements mandating physical or logical separation

**Considerations**:

- Higher operational overhead (multiple clusters to manage)
- Reduced resource utilization efficiency
- Increased infrastructure costs

**Projects**:

- <a href="https://github.com/kubernetes-sigs/cluster-api">Cluster API</a>: Declarative cluster lifecycle management
- <a href="https://github.com/kubernetes-sigs/hierarchical-namespaces">Hierarchical Namespaces</a>: Virtual cluster
  abstraction within a single cluster

### 2. Strong Isolation: Node Pool / Physical Resource Isolation

**Approach**: Assign dedicated node pools to tenants or workload types.

**Benefits**:

- Hard boundaries for CPU, memory, GPU resources
- Prevents kernel-level interference between tenants
- Simplifies capacity planning and quota enforcement

**Use Cases**:

- Mixed online/offline workloads with strict SLA requirements
- GPU-intensive AI training vs. CPU-intensive web services

**Implementation**:

```yaml
# Node pool with taints for dedicated workloads
apiVersion: v1
kind: Node
metadata:
  name: gpu-node-01
  labels:
    workload-type: ai-training
    tenant: team-a
spec:
  taints:
  - key: workload-type
    value: ai-training
    effect: NoSchedule
```

```yaml
# Pod with tolerations to schedule on dedicated nodes
apiVersion: v1
kind: Pod
metadata:
  name: training-job
spec:
  tolerations:
  - key: workload-type
    operator: Equal
    value: ai-training
    effect: NoSchedule
  nodeSelector:
    workload-type: ai-training
    tenant: team-a
  containers:
  - name: trainer
    resources:
      limits:
        nvidia.com/gpu: "8"
```

**Considerations**:

- May lead to resource fragmentation if not carefully managed
- Requires robust quota and scheduling policies

**Projects**:

- <a href="https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler">Cluster Autoscaler</a>:
  Auto-scales node pools based on demand
- <a href="https://github.com/koordinator-sh/koordinator">Koordinator</a>: Colocation scheduling with QoS guarantees

### 3. Runtime Isolation: Sandboxed Runtimes

Sandboxed runtimes provide stronger isolation than standard container runtimes by adding an additional security layer,
either through lightweight VMs or user-space kernels.

#### 3.1 gVisor: Application Kernel / Syscall Interception

<a href="https://gvisor.dev/">gVisor</a> implements a user-space kernel that intercepts and handles syscalls, reducing
the kernel attack surface.

**Key Features**:

- User-space kernel written in Go
- Syscall filtering and validation
- OCI-compatible (works with Kubernetes via RuntimeClass)
- **gVisor Snapshots**: Pre-warm container state for fast cold starts

**Use Cases**:

- CPU-only AI agent workloads
- Untrusted code execution (e.g., LLM-generated code)
- Serverless functions with security requirements

**Limitations**:

- No GPU support
- Performance overhead from syscall interception
- Some syscalls not implemented

**Configuration**:

```yaml
# RuntimeClass for gVisor
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
---
# Pod using gVisor
apiVersion: v1
kind: Pod
metadata:
  name: agent-workload
spec:
  runtimeClassName: gvisor
  containers:
  - name: agent
    image: python:3.11-slim
    command: ["python", "agent.py"]
```

**Projects**:

- <a href="https://github.com/google/gvisor">gVisor</a>
- <a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
  GKE Agent Sandbox</a>: Production-ready gVisor with snapshots (90% faster cold starts)

#### 3.2 Kata Containers: Lightweight VMs / Per-Pod Kernel

<a href="https://katacontainers.io/">Kata Containers</a> runs each Pod in a lightweight VM, providing hardware-level
isolation.

**Key Features**:

- Hardware virtualization (KVM, Firecracker, Cloud Hypervisor)
- Per-Pod kernel isolation
- GPU passthrough support (VFIO)
- OCI-compatible

**Use Cases**:

- GPU-intensive AI training and inference
- Multi-tenant inference with untrusted models
- Compliance requirements mandating VM-level isolation

**Benefits**:

- Strong security boundary (hardware isolation)
- GPU performance near-native
- Compatible with existing Kubernetes workloads

**Configuration**:

```yaml
# RuntimeClass for Kata Containers
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata
---
# GPU workload with Kata isolation
apiVersion: v1
kind: Pod
metadata:
  name: secure-inference
spec:
  runtimeClassName: kata
  containers:
  - name: model-server
    image: pytorch/torchserve:latest
    resources:
      limits:
        nvidia.com/gpu: "1"
```

**Comparison: Kata vs gVisor for AI Workloads**:

| Feature | Kata Containers | gVisor |
| --- | --- | --- |
| GPU Support | ✅ Yes | ❌ No |
| Overhead | Low (near-native) | Medium (syscall interception) |
| Boot Time | Fast (< 1s) | Very Fast (< 100ms with snapshots) |
| Memory Overhead | ~130MB per VM | ~15MB per sandbox |
| Security Model | Hardware isolation | Software isolation |
| AI Use Case | GPU training/inference | CPU-only agent workloads |

**Projects**:

- <a href="https://github.com/kata-containers/kata-containers">Kata Containers</a>
- <a href="https://github.com/firecracker-microvm/firecracker">Firecracker</a>: Lightweight VM for AWS

### 4. Confidential Computing: Confidential Containers

**Approach**: Encrypt data in use with hardware-based trusted execution environments (TEEs).

**Key Technologies**:

- **Intel SGX/TDX**: Trusted execution enclaves
- **AMD SEV/SEV-ES/SEV-SNP**: Encrypted VM memory
- **ARM TrustZone**: Secure execution environment
- **Confidential Containers**: CNCF project for TEE-based container isolation

**Benefits**:

- Protect sensitive models and data from cloud providers
- Defense against memory scraping and side-channel attacks
- Compliance with data sovereignty regulations

**Use Cases**:

- Private AI models in public clouds
- Healthcare and financial AI workloads with strict privacy requirements
- Federated learning with encrypted gradients

**Projects**:

- <a href="https://github.com/confidential-containers/confidential-containers">Confidential Containers</a>:
  CNCF Sandbox project
- <a href="https://github.com/occlum/occlum">Occlum</a>: TEE OS for confidential computing

### 5. Foundational: Container / Pod Security Constraints

These are baseline security practices that apply to all multi-tenant Kubernetes deployments.

**Key Mechanisms**:

- **Pod Security Standards**: Enforce privileged, baseline, or restricted policies
- **SecurityContext**: runAsNonRoot, readOnlyRootFilesystem, capabilities drop
- **Network Policies**: Restrict pod-to-pod communication
- **ResourceQuotas**: Limit CPU, memory, GPU per namespace
- **LimitRanges**: Default resource requests/limits

**Example**:

```yaml
# Enforcing Pod Security Standards
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-a
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
# ResourceQuota for tenant namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-a-quota
  namespace: tenant-a
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    requests.nvidia.com/gpu: "10"
    limits.cpu: "200"
    limits.memory: "400Gi"
```

**Projects**:

- <a href="https://kubernetes.io/docs/concepts/security/pod-security-standards/">Pod Security Standards</a>
- <a href="https://www.openpolicyagent.org/docs/latest/kubernetes-introduction/">OPA Gatekeeper</a>:
  Policy enforcement
- <a href="https://kyverno.io/">Kyverno</a>: Kubernetes-native policy management

### 6. Network and Storage Isolation

**Network Isolation**:

- **Network Policies**: Enforce tenant-level segmentation
- **Service Mesh**: mTLS, traffic encryption, observability
- **CNI Plugins**: Calico, Cilium, Weave for multi-tenancy

**Storage Isolation**:

- **StorageClasses**: Dedicated storage tiers per tenant
- **Volume Snapshots**: Tenant-specific backup policies
- **Encryption at Rest**: CSI drivers with encryption support

**Example**:

```yaml
# Network Policy: Deny all ingress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: tenant-a
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
# Allow specific ingress from same namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: tenant-a
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}
```

**Projects**:

- <a href="https://github.com/projectcalico/calico">Calico</a>: Network policies and security
- <a href="https://cilium.io/">Cilium</a>: eBPF-based networking and security
- <a href="https://istio.io/">Istio</a>: Service mesh with mTLS

## Agent Sandbox: Developments in Multi-Tenant AI Agent Execution

AI agents executing LLM-generated code require strong isolation to prevent untrusted code from compromising the
cluster or accessing sensitive data.

### Kubernetes Agent Sandbox Warm Pool

The **Kubernetes Agent Sandbox Warm Pool** pattern addresses the cold start problem for AI agents by maintaining a
pool of pre-initialized sandboxed environments.

**Key Concepts**:

- **Pre-Warmed Sandboxes**: Pool of ready-to-use gVisor or Kata containers
- **Fast Allocation**: Sub-second allocation of sandbox to incoming agent request
- **Lifecycle Management**: Automatic cleanup and replenishment of sandbox pool
- **Resource Efficiency**: Balance between pool size and resource waste

**Architecture**:

```text
┌─────────────────────────────────────────────────────────┐
│                   Agent Request                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Warm Pool Controller                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Sandbox 1│  │ Sandbox 2│  │ Sandbox 3│ ... (pool)  │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────┬───────────────────────────────────┘
                      │ (allocate)
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Sandbox Execution (gVisor/Kata)                 │
│  - Execute LLM-generated code                           │
│  - Resource limits enforced                             │
│  - Network policies applied                             │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼ (cleanup & recycle)
```

**Benefits**:

- **Reduced Latency**: Eliminate cold start overhead (90% improvement with gVisor snapshots)
- **Security**: Strong isolation for untrusted code
- **Scalability**: Handle burst traffic with pre-allocated resources

**Challenges**:

- **Resource Overhead**: Idle sandboxes consume memory and CPU
- **Pool Management**: Tuning pool size to balance latency and cost
- **Multi-Tenancy**: Ensuring strict isolation between tenants in shared pools

**Implementation Considerations**:

- Use gVisor snapshots for CPU-only agent workloads (fastest)
- Use Kata Containers for GPU-accelerated agent workloads
- Implement tenant-specific pools for strict isolation requirements
- Monitor pool utilization and auto-scale based on demand

### Public Cloud vs Private Cloud Considerations for Agent Sandboxes

**Public Cloud**:

- Higher security requirements (untrusted external users)
- Reliance on managed services (GKE Agent Sandbox)
- Auto-scaling warm pools based on global traffic patterns
- Cost optimization through dynamic pool sizing

**Private Cloud**:

- Controlled user base (internal employees)
- Self-hosted sandbox solutions (custom warm pools)
- Fixed pool sizes based on predictable usage patterns
- Integration with enterprise RBAC and audit systems

**Reference**:

- <a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
  GKE Agent Sandbox: Strong Guardrails for Agentic AI</a>

## Multicluster Application Management

As AI infrastructure scales, managing workloads across multiple Kubernetes clusters becomes essential for disaster
recovery, geographic distribution, and workload isolation.

### CNCF Multicluster Management (MCM) Radar 2024Q3

The CNCF Technology Radar provides guidance on the maturity of multicluster management solutions:

**Adopt** (Production-Ready):

- **<a href="https://github.com/argoproj/argo-cd">Argo CD</a>** (Graduated): GitOps continuous delivery for
  Kubernetes
- **<a href="https://github.com/cilium/cilium">Cilium</a>** (Graduated): Multi-cluster networking with Cluster Mesh

**Trial** (Evaluate for Production):

- **<a href="https://github.com/karmada-io/karmada">Karmada</a>** (Incubating): Multi-cloud multi-cluster application
  management
- **<a href="https://github.com/istio/istio">Istio</a>** (Graduated): Multi-cluster service mesh
- **<a href="https://github.com/linkerd/linkerd2">Linkerd</a>** (Graduated): Lightweight multi-cluster service mesh
- **<a href="https://github.com/kubestellar/kubestellar">KubeStellar</a>** (Sandbox): Multi-cluster workload
  deployment
- **<a href="https://github.com/kubestash/kubestash">Armada</a>** (Sandbox): Batch scheduling across clusters
- **<a href="https://github.com/backstage/backstage">Backstage</a>** (Incubating): Developer portal for multi-cluster
  visibility

**Assess** (Emerging):

- **<a href="https://github.com/kubevela/kubevela">KubeVela</a>** (Incubating): Application delivery platform
- **<a href="https://github.com/kubeedge/sedna">PipeCD</a>** (Sandbox): Progressive delivery for multi-cloud
- **<a href="https://github.com/kuma-io/kuma">Kuma</a>** (Sandbox): Universal service mesh
- **<a href="https://github.com/open-cluster-management-io/ocm">Meshery</a>** (Sandbox): Service mesh management plane
- **<a href="https://github.com/clusterpedia-io/clusterpedia">Clusterpedia</a>** (Sandbox): Multi-cluster resource
  search

**Hold** (Not Recommended):

- Solutions not meeting current production requirements

![CNCF MCM Radar 2024Q3](https://github.com/user-attachments/assets/9a9a4222-efa6-4f4c-9878-e40ed6bb5889)

### Multitenancy Spectrum

Different multicluster solutions provide varying levels of isolation, as illustrated in the multitenancy spectrum:

![Multitenancy Spectrum](https://github.com/user-attachments/assets/e463912b-9251-4bd3-a874-05b9ee7ad817)

**Namespaces** (Weakest Isolation):

- Shared cluster, shared control plane
- Lowest overhead, highest resource efficiency
- Suitable for trusted internal teams

**Namespaces as a Service**:

- Virtual clusters within a physical cluster
- Simplified multi-tenancy with namespace-level RBAC
- Projects: <a href="https://github.com/loft-sh/vcluster">vCluster</a>,
  <a href="https://github.com/kubernetes-sigs/cluster-api-provider-nested">Kamaji</a>

**Kubernetes API as a Service**:

- Managed control planes with shared worker nodes
- Examples: <a href="https://github.com/kubernetes-sigs/cluster-api-provider-nested/tree/main/controlplane">Capsule</a>,
  <a href="https://github.com/kubernetes-sigs/cluster-api">KCP</a>

**Control Plane as a Service (Internal)**:

- Shared management plane with isolated control planes per tenant
- Projects: <a href="https://github.com/kcp-dev/kcp">k3k</a>, <a href="https://github.com/loft-sh/vcluster">HNC</a>

**Control Plane as a Service (External)**:

- Full control plane isolation per tenant
- Projects: <a href="https://github.com/loft-sh/vcluster">vCluster (external mode)</a>,
  <a href="https://github.com/kcp-dev/kcp">Kamaji (external)</a>

**Dedicated Clusters** (Strongest Isolation):

- Separate Kubernetes clusters per tenant
- Highest security, highest operational overhead
- Required for untrusted multi-tenancy

### Key Multicluster Use Cases for AI Infra

**Geographic Distribution**:

- Deploy inference services close to users (multi-region)
- Comply with data residency regulations

**Disaster Recovery**:

- Replicate critical AI workloads across clusters
- Failover for high-availability inference services

**Workload Isolation**:

- Separate clusters for training vs inference
- Isolate sensitive models from general workloads

**Resource Optimization**:

- Burst workloads to public cloud during peak demand
- Use on-premises clusters for baseline workloads

**Reference**:

- <a href="https://www.cncf.io/reports/cncf-technology-radar/">CNCF Technology Radar</a>

## Best Practices for Multi-Tenant AI Infrastructure

### Layered Defense Strategy

Combine multiple isolation mechanisms for defense in depth:

1. **Cluster Isolation**: Separate untrusted tenants to dedicated clusters
2. **Node Pool Isolation**: Dedicated GPU nodes for critical workloads
3. **Runtime Isolation**: gVisor for agent workloads, Kata for GPU workloads
4. **Network Isolation**: Network policies and service mesh
5. **Storage Isolation**: Encrypted persistent volumes per tenant

### Workload-Specific Isolation

Match isolation strength to security requirements:

| Workload Type | Recommended Isolation | Rationale |
| --- | --- | --- |
| Internal Training | Standard (cgroups + namespaces) | Trusted users, performance priority |
| Multi-Tenant Inference | Enhanced (Kata Containers) | Untrusted models, GPU required |
| AI Agent Execution | Strong (gVisor with snapshots) | Untrusted code, CPU-only |
| Confidential Models | Maximum (Confidential Containers) | Regulatory compliance, TEE required |

### Monitoring and Auditing

Comprehensive observability for multi-tenant security:

- **Resource Usage**: Track per-tenant CPU, GPU, memory, storage consumption
- **Security Events**: Audit logs for privilege escalations, policy violations
- **Isolation Violations**: Alerts for namespace breaches, syscall anomalies
- **Cost Attribution**: Chargeback models for fair resource allocation

**Tools**:

- <a href="https://github.com/falcosecurity/falco">Falco</a>: Runtime security monitoring
- <a href="https://github.com/aquasecurity/tracee">Tracee</a>: eBPF-based security observability
- <a href="https://github.com/cilium/tetragon">Tetragon</a>: eBPF-based security and policy enforcement

### Public Cloud vs Private Cloud Summary

**Public Cloud**:

- Stronger isolation requirements (untrusted tenants)
- Managed services reduce operational burden (GKE, EKS, AKS)
- Auto-scaling and dynamic resource allocation
- Compliance with global regulations (GDPR, SOC2)

**Private Cloud**:

- Controlled user base (internal employees)
- Self-hosted solutions with enterprise integration
- Fixed resource pools requiring efficient scheduling
- Strict internal security policies and RBAC

## Conclusion

Multi-tenancy isolation in AI infrastructure requires a nuanced approach that balances security, performance, and
operational complexity. Public cloud and private cloud deployments have distinct requirements, as do training and
inference workloads. By layering isolation mechanisms — from cluster separation to sandboxed runtimes — and aligning
strategies with specific use cases, organizations can build secure, efficient, and scalable AI platforms.

## References

- <a href="https://kubernetes.io/docs/concepts/security/multi-tenancy/">Kubernetes Multi-Tenancy</a>
- <a href="https://www.cncf.io/blog/2023/12/15/container-isolation-gone-wrong/">CNCF: Container Isolation</a>
- <a href="https://gvisor.dev/">gVisor Official Site</a>
- <a href="https://katacontainers.io/">Kata Containers Official Site</a>
- <a href="https://github.com/confidential-containers/confidential-containers">Confidential Containers</a>
- <a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
  GKE Agent Sandbox</a>
- <a href="https://www.cncf.io/reports/cncf-technology-radar/">CNCF Technology Radar</a>
- <a href="https://mp.weixin.qq.com/s/W189KuI4QG3WEhsDLov31A">模型 - 多租户安全隔离 (Chinese Article)</a>

---

_Multi-tenancy isolation is an evolving field. As AI workloads scale and new security threats emerge, isolation
strategies will continue to adapt. This document reflects best practices as of December 2025._
