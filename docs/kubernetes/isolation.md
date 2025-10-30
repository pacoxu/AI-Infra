---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: kubernetes, isolation, security, multi-tenancy
canonical_path: docs/kubernetes/isolation.md
---

# Isolation of AI Workloads

Isolation is a critical concern for AI workloads running on Kubernetes,
especially in multi-tenant environments where security, resource boundaries,
and predictable performance are essential. This document explores various
isolation mechanisms for AI workloads in cloud-native infrastructure.

## Why Isolation Matters for AI Workloads

AI workloads present unique isolation challenges:

- **Resource Intensive**: GPU/TPU access, large memory footprints
- **Long-Running**: Training jobs may run for days or weeks
- **Multi-Tenant**: Shared infrastructure requires strong security boundaries
- **Sensitive Data**: Models and training data often contain proprietary
  or confidential information
- **Cost Optimization**: Preventing noisy neighbors and ensuring fair resource
  sharing

## 1. Control Groups (cgroups) Filesystem

Control groups (cgroups) provide the foundational isolation mechanism for
containers by managing and limiting resource usage at the kernel level.

### Key Concepts

- **Resource Controllers**: CPU, memory, I/O, network bandwidth
- **Hierarchical Organization**: Nested cgroup structures for fine-grained
  control
- **cgroups v1 vs v2**: Modern systems use unified cgroups v2 with improved
  resource management

### AI-Specific Considerations

```yaml
# Example: Kubernetes Pod with resource limits
apiVersion: v1
kind: Pod
metadata:
  name: ai-training-job
spec:
  containers:
  - name: trainer
    resources:
      limits:
        cpu: "16"
        memory: "64Gi"
        nvidia.com/gpu: "4"
      requests:
        cpu: "8"
        memory: "32Gi"
        nvidia.com/gpu: "4"
```

### Projects and Resources

- <a href="https://www.kernel.org/doc/Documentation/cgroup-v2.txt">cgroups v2
  documentation</a>
- <a href="https://github.com/opencontainers/runc">runc</a>: Reference
  implementation of OCI runtime with cgroup integration

## 2. Privilege and Security Contexts

Privilege management ensures workloads run with minimal necessary permissions,
reducing attack surface and blast radius.

### Security Context Options

- **runAsNonRoot**: Enforce non-root user execution
- **runAsUser/runAsGroup**: Specify UID/GID for containers
- **readOnlyRootFilesystem**: Prevent writes to container filesystem
- **allowPrivilegeEscalation**: Block privilege escalation attempts
- **capabilities**: Drop unnecessary Linux capabilities

### Best Practices for AI Workloads

```yaml
# Example: Secure AI workload pod
apiVersion: v1
kind: Pod
metadata:
  name: secure-ai-inference
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: model-server
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

### Projects and Resources

- <a href="https://kubernetes.io/docs/tasks/configure-pod-container/security-context/">
  Kubernetes Security Context</a>
- <a href="https://kubernetes.io/docs/concepts/security/pod-security-standards/">
  Pod Security Standards</a>

## 3. User Namespace Isolation

User namespaces provide an additional isolation layer by mapping container
UIDs/GIDs to different ranges on the host system.

### How It Works

- Container processes appear to run as root (UID 0) inside the container
- Host kernel maps these to unprivileged UIDs (e.g., 100000-165535)
- Compromised container cannot access host resources as root

### Kubernetes Support

User namespaces support is under active development in Kubernetes:

- **Alpha in v1.25**: Initial support behind feature gate
- **Beta in v1.30**: Improved stability and broader runtime support

### Configuration Example

```yaml
# Example: Pod with user namespace (requires Kubernetes v1.30+)
apiVersion: v1
kind: Pod
metadata:
  name: ai-workload-userns
spec:
  hostUsers: false  # Enable user namespace
  containers:
  - name: training
    image: pytorch/pytorch:latest
```

### Projects and Resources

- <a href="https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/127-user-namespaces">
  Kubernetes KEP-127: User Namespaces</a>
- <a href="https://man7.org/linux/man-pages/man7/user_namespaces.7.html">
  Linux user_namespaces man page</a>

## 4. Rootless Container Runtimes

Rootless containers run the entire container runtime (not just containers)
without requiring root privileges on the host.

### Benefits

- **Reduced Attack Surface**: Runtime daemon runs as regular user
- **No Root Required**: Suitable for shared HPC environments
- **Defense in Depth**: Additional isolation layer for untrusted workloads

### Implementations

#### Rootless Docker/containerd

<a href="https://docs.docker.com/engine/security/rootless/">Rootless Docker</a>
allows running Docker daemon as non-root user with user namespaces and
slirp4netns for networking.

#### Rootless Podman

<a href="https://github.com/containers/podman">Podman</a> provides native
rootless support without requiring a daemon, using fuse-overlayfs for storage.

### Kubernetes Integration

```yaml
# CRI-O configuration for rootless mode
# /etc/crio/crio.conf
[crio.runtime]
  default_runtime = "runc"
  [crio.runtime.runtimes.runc]
    runtime_path = "/usr/bin/runc"
    runtime_type = "oci"
    allowed_annotations = []
    
  # Rootless runtime configuration
  [crio.runtime.runtimes.crun-rootless]
    runtime_path = "/usr/bin/crun"
    runtime_type = "oci"
```

### Limitations for AI Workloads

- **GPU Access**: Limited or no GPU support in rootless mode
- **Performance**: Network and storage overhead with user-space drivers
- **Compatibility**: Some device plugins may not work

### Projects and Resources

- <a href="https://rootlesscontaine.rs/">Rootless Containers</a>: Community hub
- <a href="https://github.com/containers/crun">crun</a>: Fast and low-memory
  OCI runtime with rootless support

## 5. Virtual Machine-Based Isolation

VM-based isolation provides stronger security boundaries by running containers
inside lightweight virtual machines.

### Kata Containers

<a href="https://github.com/kata-containers/kata-containers">Kata Containers</a>
is an open-source project providing VM-based container isolation with OCI
compatibility.

#### Architecture

- **Hardware Virtualization**: Leverages KVM, Firecracker, or Cloud Hypervisor
- **Lightweight VMs**: Fast boot times (sub-second) with minimal overhead
- **Kubernetes Integration**: Works as a RuntimeClass

#### Example Configuration

```yaml
# RuntimeClass for Kata Containers
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata
---
# Pod using Kata Containers
apiVersion: v1
kind: Pod
metadata:
  name: ai-inference-kata
spec:
  runtimeClassName: kata
  containers:
  - name: model-server
    image: pytorch/torchserve:latest
    resources:
      limits:
        nvidia.com/gpu: "1"
```

#### GPU Support

Kata Containers supports GPU passthrough:

- Direct device assignment for bare-metal performance
- VFIO for secure device isolation
- Compatible with NVIDIA GPUs, AMD GPUs

### gVisor

<a href="https://github.com/google/gvisor">gVisor</a> provides application
kernel isolation by intercepting system calls with a user-space kernel.

#### Architecture

- **User-Space Kernel**: Implements Linux kernel interface in Go
- **Syscall Interception**: Prevents direct kernel access
- **Defense in Depth**: Reduced kernel attack surface

#### Example Configuration

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
  name: ai-workload-gvisor
spec:
  runtimeClassName: gvisor
  containers:
  - name: training
    image: tensorflow/tensorflow:latest
```

#### Limitations for AI Workloads

- **No GPU Support**: gVisor does not support GPU passthrough
- **Performance Overhead**: Syscall interception adds latency
- **Compatibility**: Some syscalls not implemented

### Comparison: Kata vs gVisor for AI

| Feature | Kata Containers | gVisor |
|---------|----------------|--------|
| GPU Support | ✅ Yes | ❌ No |
| Overhead | Low (near-native) | Medium (syscall overhead) |
| Boot Time | Fast (< 1s) | Very Fast (< 100ms) |
| Memory Overhead | ~130MB per VM | ~15MB per sandbox |
| Security Model | Hardware isolation | Software isolation |
| AI Use Case | GPU-intensive training/inference | CPU-only workloads |

### Projects and Resources

- <a href="https://katacontainers.io/">Kata Containers Official Site</a>
- <a href="https://gvisor.dev/">gVisor Official Site</a>
- <a href="https://github.com/firecracker-microvm/firecracker">Firecracker</a>:
  AWS lightweight VM for secure multi-tenant containers

## 6. Agent Sandbox (Kubernetes SIG Project)

<a href="https://github.com/kubernetes-sigs/agent-sandbox">Agent Sandbox</a>
is a Kubernetes SIG project exploring secure execution environments for AI
agents and autonomous workloads.

### Motivation

AI agents pose unique security challenges:

- **Untrusted Code Execution**: LLM-generated code needs sandboxing
- **Resource Limits**: Prevent runaway agent processes
- **Network Isolation**: Restrict external communications
- **Data Access Control**: Limit sensitive data exposure

### Design Principles

1. **Multiple Isolation Layers**: Combine namespace, cgroup, seccomp, AppArmor
2. **Resource Quotas**: Enforce strict CPU, memory, network limits
3. **Time Limits**: Automatic termination of long-running agents
4. **Audit Logging**: Comprehensive tracking of agent actions

### Example Use Cases

- Code interpreters for LLM agents (e.g., ChatGPT Code Interpreter)
- Autonomous workflow execution (e.g., function calling)
- Dynamic model deployment and testing
- Safe execution of user-provided inference code

### Current Status

The project is in early development (as of 2025). Key areas:

- Defining isolation requirements for agent workloads
- Integrating with Kubernetes security primitives
- Exploring WebAssembly (Wasm) for sandboxing
- Collaboration with AI Gateway and Agentic Workflow projects

### Projects and Resources

- <a href="https://github.com/kubernetes-sigs/agent-sandbox">Agent Sandbox
  GitHub Repository</a>
- Related: <a href="https://github.com/kagent-dev/kagent">KAgent</a>
  (CNCF Sandbox)

## 7. Checkpoint and Restore

Checkpoint/Restore allows saving and restoring the complete state of running
containers, enabling workload migration, fault tolerance, and efficient
resource utilization. This is particularly relevant for AI workloads using GPUs,
where checkpoint/restore can enable efficient resource utilization and fault
tolerance for long-running training jobs.

### Kubernetes Working Group

The Kubernetes community has active working groups focused on checkpoint/restore
capabilities:

- <a href="https://github.com/kubernetes/community/blob/master/wg-batch/README.md">
  Kubernetes WG Batch</a>: Coordinates batch workload features including
  checkpoint/restore for training jobs
- <a href="https://kccnceu2025.sched.com/event/1tx7i">KubeCon EU 2025:
  Checkpoint/Restore in Kubernetes</a>: Community discussion on GPU
  checkpoint/restore scenarios

### CRIU (Checkpoint/Restore In Userspace)

<a href="https://github.com/checkpoint-restore/criu">CRIU</a> is the core
technology for checkpointing Linux processes.

#### How It Works

1. **Checkpoint**: Freeze process, dump memory, file descriptors, and state
2. **Storage**: Serialize state to filesystem or object storage
3. **Restore**: Recreate process with exact same state on same/different host

#### GPU Plugin Architecture

CRIU supports GPU checkpoint/restore through a plugin architecture:

- <a href="https://github.com/checkpoint-restore/criu/tree/criu-dev/plugins">
  CRIU Plugins</a>: Extensible plugin system for device-specific checkpointing
- **CUDA Plugin**: Handles NVIDIA GPU state and CUDA contexts
- **AMD GPU Plugin**: Handles AMD GPU state via AMDGPU driver

### GPU Checkpoint/Restore Support

GPU checkpoint/restore is critical for AI workloads, enabling efficient
resource utilization and fault tolerance for long-running training jobs.

#### NVIDIA CUDA Checkpoint

<a href="https://github.com/NVIDIA/cuda-checkpoint">NVIDIA cuda-checkpoint</a>
is a utility for checkpointing CUDA applications, built on top of CRIU.

**Key Features:**

- **CUDA Context Preservation**: Saves GPU memory, CUDA streams, and contexts
- **Driver Compatibility**: Requires CUDA driver version 550 or higher
- **Application Transparency**: Minimal code changes required for checkpointing
- **Multi-GPU Support**: Handles applications using multiple GPUs

**Requirements:**

- NVIDIA GPU driver 550+
- CRIU with CUDA plugin support
- Compatible container runtime (containerd, CRI-O)

**Use Cases for AI:**

- **Training Checkpoints**: Save training state across preemptions
- **Model Migration**: Move running inference workloads between nodes
- **Fault Tolerance**: Resume training after hardware failures
- **Cost Optimization**: Migrate to spot/preemptible GPU instances

#### PyTorch Support

PyTorch applications can benefit from GPU checkpoint/restore:

- <a href="https://developer.nvidia.com/blog/checkpointing-cuda-applications-with-criu/">
  NVIDIA Blog: Checkpointing CUDA Applications with CRIU</a>: Technical
  overview of PyTorch checkpoint/restore
- <a href="https://github.com/NVIDIA/cuda-checkpoint/issues/4">PyTorch
  Support Discussion</a>: Community discussion and implementation details

**Integration Pattern:**

```python
# PyTorch training with checkpoint-friendly patterns
import torch

def train_with_checkpointing():
    model = MyModel().cuda()
    optimizer = torch.optim.Adam(model.parameters())
    
    # Training loop designed for checkpoint/restore
    for epoch in range(num_epochs):
        # Regular PyTorch training
        loss = train_epoch(model, optimizer)
        
        # Application-level checkpoint (model weights)
        torch.save({
            'epoch': epoch,
            'model_state': model.state_dict(),
            'optimizer_state': optimizer.state_dict(),
        }, f'checkpoint_{epoch}.pt')
        
        # CRIU can checkpoint at this point with full CUDA state
```

#### AMD GPU Support

AMD GPU checkpoint/restore is supported through CRIU plugins:

- **AMDGPU Plugin**: Part of CRIU plugin ecosystem
- **ROCm Compatibility**: Works with AMD ROCm stack
- **Driver Requirements**: Requires compatible AMDGPU driver version

**Combined CUDA + AMDGPU Support:**

The CRIU plugin architecture enables checkpoint/restore for heterogeneous
GPU environments:

- NVIDIA GPUs via cuda-checkpoint
- AMD GPUs via AMDGPU plugin
- Mixed GPU deployments in the same Kubernetes cluster

### Kubernetes Integration

Checkpoint/Restore support in Kubernetes:

- **Forensic Container Checkpointing (KEP-2008)**: Alpha in v1.25
- **CRI Support**: Container runtime must implement checkpoint APIs
- **CSI Integration**: Store checkpoints in persistent volumes

#### Example Usage

```bash
# Checkpoint a container using crictl
crictl checkpoint <container-id> <checkpoint-name>

# Restore from checkpoint
crictl restore <checkpoint-name> <pod-id>
```

### AI Workload Benefits

#### Training Checkpoints

- **Fault Tolerance**: Resume training after node failures
- **Cost Optimization**: Migrate to spot/preemptible instances
- **Experimentation**: Save/restore model states for A/B testing

#### Inference Checkpoints

- **Fast Warmup**: Pre-warmed model caches and GPU state
- **Migration**: Move inference workloads across regions
- **Scaling**: Rapid scale-out with checkpointed replicas

### Implementation Considerations

```yaml
# Example: Checkpoint-friendly Pod configuration
apiVersion: v1
kind: Pod
metadata:
  name: checkpointable-training
  annotations:
    checkpoint.kubernetes.io/enabled: "true"
spec:
  restartPolicy: Never  # Required for forensic checkpointing
  containers:
  - name: trainer
    image: pytorch/pytorch:latest
    volumeMounts:
    - name: checkpoint-storage
      mountPath: /checkpoints
  volumes:
  - name: checkpoint-storage
    persistentVolumeClaim:
      claimName: training-checkpoints
```

### Challenges for GPU Workloads

GPU checkpoint/restore presents unique challenges, but recent advances have
made it more practical:

- **GPU State Complexity**: CUDA contexts, device memory, and driver state
  - **Solution**: NVIDIA cuda-checkpoint (driver 550+) and CRIU plugins handle
    this automatically
- **Driver Compatibility**: Restore requires same GPU driver version
  - **Mitigation**: Container images with pinned driver versions, driver
    version matching in scheduler
- **Large State Size**: Models with billions of parameters create large
  checkpoint files
  - **Optimization**: Incremental checkpointing, compression, and fast storage
    (NVMe, object storage)
- **Cross-Vendor Support**: Different checkpoint formats for NVIDIA vs AMD
  - **Progress**: CRIU plugin architecture enables unified interface for
    NVIDIA (cuda-checkpoint) and AMD (AMDGPU plugin)

### Projects and Resources

- <a href="https://criu.org/">CRIU Official Site</a>
- <a href="https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2008-forensic-container-checkpointing">
  Kubernetes KEP-2008: Forensic Container Checkpointing</a>
- <a href="https://github.com/NVIDIA/cuda-checkpoint">NVIDIA cuda-checkpoint</a>:
  GPU checkpoint/restore utility for CUDA applications (driver 550+)
- <a href="https://github.com/checkpoint-restore/criu/tree/criu-dev/plugins">
  CRIU Plugins</a>: Plugin architecture for CUDA and AMDGPU support
- <a href="https://developer.nvidia.com/blog/checkpointing-cuda-applications-with-criu/">
  NVIDIA Blog: Checkpointing CUDA Applications with CRIU</a>
- <a href="https://github.com/NVIDIA/cuda-checkpoint/issues/4">PyTorch
  Checkpoint/Restore Support</a>: Community discussion and implementation
- <a href="https://kccnceu2025.sched.com/event/1tx7i">KubeCon EU 2025:
  Checkpoint/Restore in Kubernetes</a>: GPU checkpoint/restore scenarios
- <a href="https://github.com/kubernetes/community/blob/master/wg-batch/README.md">
  Kubernetes WG Batch</a>: Batch workload features including checkpoint/restore

## Best Practices for AI Workload Isolation

### Multi-Layer Defense

Combine multiple isolation mechanisms:

1. **Base Layer**: cgroups + namespace isolation
2. **Security Layer**: SecurityContext + Pod Security Standards
3. **Enhanced Layer**: User namespaces + rootless (where applicable)
4. **Strong Layer**: VM-based isolation (Kata) for untrusted code

### Workload Categorization

Match isolation strength to threat model:

| Workload Type | Isolation Level | Recommended Approach |
|---------------|----------------|---------------------|
| Trusted Internal Training | Standard | cgroups + SecurityContext |
| Multi-Tenant Inference | Enhanced | + User namespaces |
| External User Code | Strong | Kata Containers + Agent Sandbox |
| Sensitive Data Processing | Maximum | Kata + Encryption + Net Policy |

### Performance vs Security Trade-offs

- **Training**: Prioritize performance, accept standard isolation
- **Inference**: Balance latency requirements with security needs
- **Agent Execution**: Maximize security, accept performance overhead

## Monitoring and Observability

Track isolation effectiveness:

- **Resource Usage**: Monitor cgroup metrics for limit enforcement
- **Security Events**: Audit logs for privilege escalation attempts
- **Performance Impact**: Measure overhead of isolation mechanisms
- **Isolation Violations**: Alert on namespace or capability breaches

### Tools

- <a href="https://github.com/falcosecurity/falco">Falco</a>: Runtime
  security monitoring
- <a href="https://github.com/aquasecurity/tracee">Tracee</a>: eBPF-based
  security observability
- <a href="https://github.com/cilium/tetragon">Tetragon</a>: eBPF-based
  security observability and enforcement

## Future Directions

### Emerging Technologies

- **Confidential Computing**: SGX, SEV, TDX for encrypted memory
- **WebAssembly**: Lightweight sandboxing for agent code
- **eBPF-based Isolation**: Fine-grained syscall filtering and enforcement
- **AI-Specific Isolation**: Model watermarking, inference-time security

### Kubernetes Enhancements

- **Mature User Namespaces**: Broader runtime support and stability
- **GPU Checkpoint/Restore**: Production-ready support for GPU state migration
  with NVIDIA cuda-checkpoint (driver 550+) and AMD AMDGPU plugin integration
- **Agent Security Policies**: Purpose-built primitives for AI agents
- **Zero-Trust Networking**: Service mesh integration for AI workloads

## References

- <a href="https://kubernetes.io/docs/concepts/security/">Kubernetes
  Security Documentation</a>
- <a href="https://github.com/kubernetes/community/blob/master/wg-batch/README.md">
  Kubernetes WG Batch</a>
- <a href="https://github.com/kubernetes/community/blob/master/wg-device-management/README.md">
  Kubernetes WG Device Management</a>
- <a href="https://www.cncf.io/blog/2023/12/15/container-isolation-gone-wrong/">
  CNCF: Container Isolation Gone Wrong</a>
- <a href="https://kubernetes.io/blog/2023/08/14/forensic-container-analysis/">
  Kubernetes Blog: Forensic Container Checkpointing</a>

---

_This document covers isolation mechanisms for AI workloads in cloud-native
environments. As technologies evolve, best practices and tooling will continue
to mature._
