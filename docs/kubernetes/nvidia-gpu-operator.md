---
status: Active
maintainer: pacoxu
last_updated: 2025-10-31
tags: kubernetes, nvidia, gpu, dra, device-plugin, gpu-operator
canonical_path: docs/kubernetes/nvidia-gpu-operator.md
---

# NVIDIA GPU Operator

The <a href="https://github.com/NVIDIA/gpu-operator">NVIDIA GPU
Operator</a> streamlines the deployment and management of NVIDIA GPU
resources in Kubernetes clusters by automating the installation and lifecycle
management of GPU drivers, container runtime, device plugins, and monitoring
tools.

## Overview

The GPU Operator leverages the Kubernetes Operator pattern to manage all
NVIDIA software components required to run GPU-accelerated workloads. It
eliminates the need to manually install and configure GPU drivers and CUDA
libraries on each node.

### Key Features

- Automated GPU driver installation and upgrades
- Container runtime configuration (nvidia-container-toolkit)
- Device plugin deployment for GPU resource management
- GPU monitoring and telemetry (DCGM Exporter)
- Support for multiple GPU architectures and configurations
- Dynamic Resource Allocation (DRA) integration (upcoming)

## Core Components

### 1. Device Plugin (Current Default)

<a href="https://github.com/NVIDIA/k8s-device-plugin">**NVIDIA Device
Plugin**</a> enables GPU resource management through Kubernetes' traditional
device plugin framework.

**Key Features:**

- Advertises GPUs to kubelet
- Supports GPU sharing via time-slicing
- MIG (Multi-Instance GPU) support
- GPU resource allocation and tracking

**Usage:**

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

### 2. DRA Driver for GPUs (Future Direction)

<a href="https://github.com/NVIDIA/k8s-dra-driver-gpu">**NVIDIA DRA Driver for
GPUs**</a> provides next-generation GPU resource management using Dynamic
Resource Allocation, offering more flexible and topology-aware scheduling.

**Architecture:**

The DRA driver includes two kubelet plugins:

- <a href="https://github.com/NVIDIA/k8s-dra-driver-gpu/tree/main/cmd/gpu-kubelet-plugin">**gpu-kubelet-plugin**</a>:
  Standard GPU resource allocation plugin
- <a href="https://github.com/NVIDIA/k8s-dra-driver-gpu/tree/main/cmd/compute-domain-kubelet-plugin">**compute-domain-kubelet-plugin**</a>:
  Advanced plugin for compute domain management

**Advanced Capabilities:**

- GB200 support with specialized compute domain management
- Topology-aware GPU scheduling (NVLink, NVSwitch awareness)
- Fine-grained resource allocation
- Support for complex multi-GPU configurations

**GB200 Support:**

The DRA driver provides enhanced support for NVIDIA GB200 Grace Blackwell
Superchip platforms through specialized compute domain management. For
technical details, see the
<a href="https://docs.google.com/presentation/d/1Xupr8IZVAjs5bNFKJnYaK0LE7QWETnJjkz6KOfLu87E/edit?pli=1&slide=id.g373e0ebfa8e_1_233#slide=id.g373e0ebfa8e_1_233">GB200
DRA Architecture Presentation</a>.

**Integration Roadmap:**

DRA driver will be integrated into GPU Operator in future releases, providing
a migration path from device plugin to DRA-based resource management.

**See also:** [Dynamic Resource Allocation (DRA)](./dra.md) for comprehensive
coverage of DRA concepts and usage patterns.

### 3. Driver Manager

<a href="https://github.com/NVIDIA/k8s-driver-manager">**Driver
Manager**</a> automates NVIDIA GPU driver installation and lifecycle
management on Kubernetes nodes.

**Features:**

- Automatic driver version detection and installation
- Node-specific driver configuration
- Driver upgrade coordination
- Support for multiple driver versions across nodes

### 4. DCGM Exporter

<a href="https://github.com/NVIDIA/dcgm-exporter">**DCGM Exporter**</a>
provides GPU telemetry and monitoring by exposing metrics from NVIDIA Data
Center GPU Manager (DCGM) to Prometheus.

**Metrics Provided:**

- GPU utilization and temperature
- Memory usage and errors
- Power consumption
- PCIe throughput
- Clock frequencies
- ECC errors and health status

## Additional Components

The GPU Operator manages several additional components for specialized use
cases:

### Runtime and Discovery

- **NVIDIA GPU Feature Discovery**: Automatically discovers and labels GPU
  capabilities on nodes
- **GPU Driver**: NVIDIA datacenter GPU drivers
- **Container Toolkit**: nvidia-container-toolkit for container runtime
  integration

### Advanced Features

- **MIG Manager**: Multi-Instance GPU configuration and management
- **Validator**: Post-deployment validation of GPU stack
- **DCGM**: NVIDIA Data Center GPU Manager for health monitoring
- **KubeVirt GPU Device Plugin**: GPU support for virtualized workloads
- **vGPU Manager**: Virtual GPU management for virtualization platforms

### Specialized Configurations

- **GDS Driver**: GPUDirect Storage driver for direct GPU-to-storage transfers
- **Confidential Computing Manager**: TEE (Trusted Execution Environment)
  support for GPU workloads
- **Kata Manager**: GPU support for Kata Containers runtime
- **GDRCopy Driver**: GPUDirect RDMA support for high-speed network transfers

## Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- GPU-enabled nodes with NVIDIA GPUs
- Node Feature Discovery (NFD) Operator (recommended)

### Installation

Install via Helm:

```bash
# Add NVIDIA Helm repository
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install GPU Operator
helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace
```

### Verification

```bash
# Check GPU Operator pods
kubectl get pods -n gpu-operator

# Verify GPU resources
kubectl get nodes -o=custom-columns=NAME:.metadata.name,GPUs:.status.capacity."nvidia\.com/gpu"

# Test GPU workload
kubectl run gpu-test --image=nvidia/cuda:12.0.0-base-ubuntu20.04 \
  --limits=nvidia.com/gpu=1 -- nvidia-smi
```

## Configuration

### Device Plugin Configuration

Configure GPU sharing and resource policies:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: device-plugin-config
  namespace: gpu-operator
data:
  config.yaml: |
    version: v1
    sharing:
      timeSlicing:
        replicas: 4
    mig:
      strategy: mixed
```

### DCGM Exporter Configuration

Customize metrics collection:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dcgm-exporter-config
  namespace: gpu-operator
data:
  metrics.csv: |
    # GPU utilization
    DCGM_FI_DEV_GPU_UTIL, gauge, GPU utilization
    # Memory usage
    DCGM_FI_DEV_FB_USED, gauge, GPU memory used
    DCGM_FI_DEV_FB_FREE, gauge, GPU memory free
```

## Best Practices

### Production Deployment

- Use Node Feature Discovery (NFD) for automatic node labeling
- Configure resource quotas and limits for GPU namespaces
- Enable DCGM metrics collection for monitoring
- Set up alerts for GPU errors and thermal events
- Use GPU time-slicing judiciously (impacts performance)

### Upgrade Strategy

- Test GPU Operator upgrades in staging environment
- Review driver compatibility matrix before upgrading
- Plan for node maintenance windows during driver upgrades
- Monitor workloads during and after upgrades

### Troubleshooting

Common issues and solutions:

```bash
# Check GPU Operator logs
kubectl logs -n gpu-operator -l app=nvidia-device-plugin-daemonset

# Verify driver installation
kubectl exec -n gpu-operator <driver-pod> -- nvidia-smi

# Check device plugin registration
kubectl get nodes -o json | jq '.items[].status.allocatable'

# Validate DCGM metrics
kubectl port-forward -n gpu-operator <dcgm-pod> 9400:9400
curl http://localhost:9400/metrics
```

## Migration Path: Device Plugin to DRA

NVIDIA is actively developing the DRA driver as the next-generation GPU
resource management solution. The migration path includes:

### Current State (Device Plugin)

- Stable and production-ready
- Simple resource model (`nvidia.com/gpu`)
- Limited topology awareness
- Good for basic GPU allocation

### Future State (DRA Driver)

- Enhanced topology awareness
- Fine-grained resource allocation
- Support for complex multi-device workloads
- Better integration with advanced GPU features (GB200, NVLink)

### Transition Strategy

1. **Evaluation Phase**: Test DRA driver in development clusters
2. **Coexistence Phase**: Run both device plugin and DRA driver
3. **Migration Phase**: Gradually migrate workloads to DRA
4. **Completion Phase**: Deprecate device plugin usage

The GPU Operator will support both approaches during the transition period,
allowing operators to choose based on their requirements.

## Learning Resources

### Official Documentation

- <a href="https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/index.html">NVIDIA
  GPU Operator Documentation</a>
- <a href="https://github.com/NVIDIA/gpu-operator">GPU Operator GitHub
  Repository</a>
- <a href="https://github.com/NVIDIA/k8s-device-plugin">NVIDIA Device Plugin
  Documentation</a>
- <a href="https://github.com/NVIDIA/k8s-dra-driver-gpu">NVIDIA DRA Driver
  Documentation</a>

### Conference Talks

- **KubeCon NA 2024**: <a href="https://www.youtube.com/watch?v=Z_15EyXOnhU">Kubernetes
  WG Device Management - GPUs, TPUs, NICs and More With DRA</a> - Kevin Klues
  & Patrick Ohly
- **NVIDIA GTC Sessions**: Search for "GPU Operator" and "Kubernetes" topics

### Community Resources

- <a href="https://github.com/kubernetes/community/blob/master/wg-device-management/README.md">Kubernetes
  WG Device Management</a>
- <a href="https://github.com/NVIDIA/gpu-operator/issues">GPU Operator Issue
  Tracker</a>
- NVIDIA Developer Forums: Cloud Native section

## Related Topics

- **[Dynamic Resource Allocation (DRA)](./dra.md)**: Understanding DRA
  concepts and architecture
- **[Scheduling Optimization](./scheduling-optimization.md)**: GPU scheduling
  strategies and best practices
- **[Node Resource Interface (NRI)](./nri.md)**: Fine-grained container
  resource management
- **[Workload Isolation](./isolation.md)**: GPU checkpoint/restore for fault
  tolerance

## RoadMap

Ongoing development and proposals:

- DRA driver integration into GPU Operator (in progress)
- Enhanced GB200 support with compute domain management
- Multi-GPU topology optimization
- Improved GPU health monitoring and diagnostics
- Cross-node GPU fabric management (NVLink, NVSwitch)
- TEE (Trusted Execution Environment) for confidential GPU computing

For the latest updates, follow:

- <a href="https://github.com/NVIDIA/gpu-operator/issues">GPU Operator
  Issues</a>
- <a href="https://github.com/NVIDIA/k8s-dra-driver-gpu/issues">DRA Driver
  Issues</a>
- <a href="https://github.com/kubernetes/enhancements/issues/?q=is%3Aissue%20DRA%20in%3Atitle">Kubernetes
  DRA KEPs</a>

---

**Note**: Some information about upcoming features (particularly DRA
integration) reflects planned functionality. Check official documentation for
current implementation status.
