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

#### gVisor Snapshots for Fast Cold Starts

gVisor supports container snapshots that enable rapid restoration of
pre-initialized containers:

- **Pre-Warmed State**: Capture initialized runtime, loaded libraries,
  dependencies
- **Fast Restore**: Restore from snapshot instead of cold starting from image
- **Consistent Performance**: Eliminate initialization variance across starts
- **Production Use**: Proven in GKE Agent Sandbox with 90% cold start
  improvement

This is particularly valuable for AI agent workloads that need rapid,
on-demand execution with strong isolation guarantees.

#### Limitations for AI Workloads

- **No GPU Support**: gVisor does not support GPU passthrough (suitable for
  CPU-only agent workloads)
- **Performance Overhead**: Syscall interception adds latency (mitigated by
  snapshots)
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

## 6. Agent Sandbox

Agent sandboxes provide secure execution environments for AI agents that can
execute arbitrary code, access tools, and interact with external systems.
Unlike traditional workload isolation, agent sandboxes must handle untrusted
LLM-generated code while supporting fast startup and high concurrency.

### Core Requirements

A production-grade agent sandbox must satisfy:

1. **Fast cold start**: Ideally under 100ms, enabling responsive agent
   invocation
2. **Strong security**: Effective isolation of untrusted code, preventing
   privilege escalation
3. **Python support**: Compatibility with common Python libraries used by
   agents
4. **Convenient image building**: Simple workflow to build and deploy custom
   agent images

### Two Architecture Patterns

When agents can execute arbitrary code, two fundamental architecture patterns
emerge for keeping secrets and infrastructure safe:

**Pattern 1: Isolate the Tool**

The agent loop runs on your infrastructure. Dangerous operations (code
execution, terminal access) run in a separate sandbox. The agent calls the
sandbox via HTTP. Code runs in an isolated environment with nothing to leak.

```text
┌──────────────────────────────┐
│        Your Backend          │
│  ┌───────────────────────┐   │
│  │    Agent Loop         │   │      ┌─────────────┐
│  │  (on your infra)      │───┼─────▶│   Sandbox   │
│  └───────────────────────┘   │ HTTP │  (terminal, │
│                              │      │   code exec) │
└──────────────────────────────┘      └─────────────┘
```

This pattern is simpler to adopt but the agent still runs alongside your
backend — a memory-hungry agent can slow down the API, and a redeployment
kills all running agents.

**Pattern 2: Isolate the Agent**

The entire agent runs in a sandbox with zero secrets. It communicates with
the outside world through a control plane that holds all credentials. The
agent becomes completely disposable: no secrets to steal, no state to
preserve.

```text
┌────────────┐   session token   ┌──────────────────┐
│   Sandbox  │──────────────────▶│  Control Plane   │
│  (agent,   │◀──────────────────│  (credentials,   │
│  zero      │   results/data    │   LLM proxy,     │
│  secrets)  │                   │   file storage)  │
└────────────┘                   └──────────────────┘
```

The control plane proxies all sensitive operations:

- **LLM calls**: Sandbox sends only new messages; control plane reconstructs
  full conversation history from the database
- **File sync**: Sandbox requests presigned URLs and uploads directly to
  object storage — never seeing cloud credentials
- **Billing and cost caps**: Enforced at the control plane level

Key insight from
<a href="https://browser-use.com/posts/two-ways-to-sandbox-agents">Browser
Use</a>: *"Your agent should have nothing worth stealing and nothing worth
preserving."*

Pattern 2 is preferred for production: each layer (sandboxes, control plane)
scales independently based on its own bottleneck.

### Sandbox Technology Comparison

Different technologies offer distinct tradeoffs for agent sandboxing:

| Technology | Cold Start | Security | Python Support | Image Build |
| ---------- | --------- | -------- | -------------- | ----------- |
| Container (Docker) | ~50ms | Shared kernel | Full | Docker |
| Firecracker microVM | ~125ms (+snapshot <1s) | Strong (separate kernel) | Full | ext4 rootfs |
| Kata Containers | ~125ms | Strong (separate kernel) | Full | OCI/Docker |
| WASM (monty) | 0.06ms | Sandboxed | Limited subset | Custom |
| Unikernel (Unikraft) | <100ms | Very strong | Improving | Custom |

#### Container-based Sandboxing

Containers start in under 50ms (excluding image pull) by running only
namespace + cgroup setup and process initialization. While fast, they share
the host kernel, which is the primary security concern for untrusted agent
code.

#### Firecracker-based Sandboxing (e2b)

<a href="https://github.com/e2b-dev/e2b">`e2b`</a> is a widely adopted
open-source agent sandbox using Firecracker microVMs. Key design choices:

- **Template = snapshot**: The sandbox image is a serialized running VM
  (filesystem + all processes). Any new sandbox can resume from this snapshot
  in under 1 second (Intel: <8ms, AMD: <3ms), dramatically reducing
  effective cold start time
- **Image building**: Converts Dockerfile to ext4 rootfs — a multi-step
  process involving image extraction, provisioning inside a VM, then
  snapshotting
- **Scheduling**: Uses a lightweight best-of-k scheduler (not Kubernetes).
  Picks the k least-loaded nodes based on CPU, memory, and active sandbox
  count — well-suited for the short lifecycle, high-concurrency nature of
  agent workloads

```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()
sbx.beta_pause()          # Serialize to snapshot

same_sbx = sbx.connect()  # Resume from snapshot in <1s
```

#### Kata Containers-based Sandboxing (k7)

<a href="https://github.com/Katakate/k7">`k7`</a> and similar Kata-based
approaches use Kata Containers (with Firecracker VMM) to get strong VM
isolation while staying compatible with standard OCI container images.

- **Image building**: Just a regular Dockerfile — no ext4 conversion needed
- **Scheduling**: Integrates with Kubernetes or k3s natively
- **Tradeoff**: Kata's abstraction layer prevents direct use of Firecracker
  snapshots, so resume speed is slower than e2b

Kata is a better fit for teams already on Kubernetes who value OCI
compatibility over snapshot-based fast resume.

#### WASM/Python Subset (monty)

<a href="https://github.com/pydantic/monty">`monty`</a> is a WASM-based
Python-subset interpreter with 0.06ms cold start. However, it does not
support Python's `class` keyword, `sys` module, or most standard library
features, making it unsuitable for general agent workloads. Pyodide (full
CPython in WASM) is an alternative but has a very slow initial load time.

#### Unikernel (Unikraft)

Unikernels compile the application and a minimal kernel into a single image
running on hardware virtualization. They offer:

- Minimal attack surface (no unused kernel features, no shell)
- Millisecond-level startup
- Very small image sizes

<a href="https://unikraft.org/">`Unikraft`</a> added limited multi-process
support (via `vfork`+`execve`) in v0.19 (May 2025), which is a prerequisite
for Python compatibility. Browser Use uses Unikraft microVMs in production
for their Pattern 2 sandbox deployment.

The main remaining challenge for unikernels is Python ecosystem compatibility
— multi-process support is still maturing. As the ecosystem evolves,
unikernels represent a strong future option: near-VM security with a very
small footprint.

Reference: <a href="https://gaocegege.com/Blog/genai/unikernel-agent">Agent
sandbox 可能的选型以及 unikernel 的机会</a> (2026) by 高策 (gaocegege)

### Image Build and Distribution Optimization

For large agent images, image pulling is often the dominant latency source
— far larger than the container/VM startup itself. Traditional Docker pull
is sequential: download N gzip layers (~2 GiB/s), single-thread decompress
(~80 MiB/s), unpack to filesystem. An 8 GB image can take over a minute.

<a href="https://modal.com">Modal</a> addresses this with **lazy loading via
FUSE**: generate a placeholder filesystem tree from the image metadata, then
fetch file data only when accessed, following a priority chain:

1. In-memory cache
2. Local SSD
3. Same-zone cache server
4. Regional CDN
5. Object storage

Similar approaches include
<a href="https://github.com/containerd/stargz-snapshotter">estargz</a> and
<a href="https://github.com/dragonflydb/dragonfly">Dragonfly</a>, which use
chunk-level content-addressable storage to enable lazy loading.

### Kubernetes SIG Agent Sandbox

<a href="https://github.com/kubernetes-sigs/agent-sandbox">Agent Sandbox</a>
is a Kubernetes SIG project exploring secure execution environments for AI
agents and autonomous workloads.

#### Design Principles

1. **Multiple Isolation Layers**: Combine namespace, cgroup, seccomp, AppArmor
2. **Resource Quotas**: Enforce strict CPU, memory, network limits
3. **Time Limits**: Automatic termination of long-running agents
4. **Audit Logging**: Comprehensive tracking of agent actions

#### Example Use Cases

- Code interpreters for LLM agents (e.g., ChatGPT Code Interpreter)
- Autonomous workflow execution (e.g., function calling)
- Dynamic model deployment and testing
- Safe execution of user-provided inference code

### GKE Agent Sandbox

<a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
GKE Agent Sandbox</a> provides production-ready strong guardrails for agentic
AI on Kubernetes and GKE, combining gVisor sandboxing with advanced snapshot
capabilities.

#### Key Features

- **gVisor Integration**: User-space kernel for strong isolation of untrusted
  agent code
- **Container Snapshots**: Pre-warmed container images with initialized
  dependencies and runtime state
- **Fast Cold Starts**: Up to 90% improvement in cold start performance
  compared to traditional container startup
- **Security Boundaries**: Hardware-level isolation for multi-tenant AI agent
  workloads

#### Performance Benefits

- **Reduced Latency**: 90% faster cold starts enable near-instant agent
  execution
- **Resource Efficiency**: Snapshot reuse reduces redundant initialization
- **Scalability**: Rapid scale-out of agent workloads for high-concurrency
  scenarios
- **Cost Optimization**: Faster startup means more efficient resource
  utilization

### Projects and Resources

- <a href="https://github.com/kubernetes-sigs/agent-sandbox">Kubernetes SIG
  Agent Sandbox</a>
- <a href="https://github.com/e2b-dev/e2b">e2b</a>: Open-source Firecracker
  agent sandbox with snapshot-based fast resume
- <a href="https://github.com/Katakate/k7">k7</a>: Kata Containers-based
  agent sandbox with OCI image support
- <a href="https://unikraft.org/">Unikraft</a>: Unikernel framework with
  multi-process support (v0.19+)
- <a href="https://github.com/pydantic/monty">monty</a>: WASM Python-subset
  interpreter for ultra-fast cold starts
- <a href="https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke">
  GKE Agent Sandbox: Strong Guardrails for Agentic AI</a>
- <a href="https://browser-use.com/posts/two-ways-to-sandbox-agents">
  Browser Use: Building Secure, Scalable Agent Sandbox Infrastructure</a>
- <a href="https://gaocegege.com/Blog/genai/unikernel-agent">高策: Agent
  sandbox 可能的选型以及 unikernel 的机会</a>

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

*This document covers isolation mechanisms for AI workloads in cloud-native
environments. As technologies evolve, best practices and tooling will continue
to mature.*
