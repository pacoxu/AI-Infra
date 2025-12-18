---
status: Active
maintainer: pacoxu
last_updated: 2025-12-17
tags: kubernetes, gpu, fault-detection, self-healing, observability, dcgm
canonical_path: docs/kubernetes/gpu-fault-detection.md
---

# GPU Fault Detection and Self-Healing in Kubernetes

Comprehensive guide to detecting, diagnosing, and automatically recovering from
GPU failures in Kubernetes clusters running AI/ML workloads.

## Table of Contents

- [Overview](#overview)
- [Common GPU Fault Types](#common-gpu-fault-types)
- [Fault Detection Approaches](#fault-detection-approaches)
- [Fault Semantics and Kubernetes Integration](#fault-semantics-and-kubernetes-integration)
- [Progressive Remediation Strategies](#progressive-remediation-strategies)
- [Fault-Aware Scheduling](#fault-aware-scheduling)
- [Job-Level Attribution and Billing](#job-level-attribution-and-billing)
- [Production Implementation](#production-implementation)
- [References](#references)

## Overview

GPU failures in Kubernetes clusters running AI workloads can cause significant
downtime, wasted compute resources, and training interruptions. Effective GPU
fault detection and self-healing requires:

1. **Comprehensive monitoring** of GPU health signals

2. **Standardized fault semantics** that Kubernetes can understand

3. **Progressive remediation** to minimize impact on running workloads

4. **Fault-aware scheduling** to avoid problematic nodes/devices

5. **Attribution** to understand which workloads triggered issues

This guide synthesizes industry best practices from ByteDance, Microsoft AKS,
NVIDIA, and the Kubernetes community.

## Common GPU Fault Types

Based on production experience, GPU faults fall into four main categories:

### 1. Card Dropout (掉卡故障)

**Symptoms:**

- GPU suddenly disappears from `nvidia-smi` output
- XID 79: GPU has fallen off the bus
- Driver reports GPU as "not found"
- DCGM health check shows GPU unavailable

**Common Causes:**

- PCIe link instability
- Power delivery issues
- Hardware failure
- Driver crashes

**Detection Signals:**

- XID 79 errors in kernel logs
- DCGM Exporter: `DCGM_FI_DEV_XID_ERRORS` metric
- `nvidia-smi` return code non-zero
- Missing GPU device files in `/dev/nvidia*`

### 2. Link Failures (链路故障)

**Symptoms:**

- NVLink bandwidth degradation
- XID 74: NVLink training errors
- Reduced multi-GPU communication performance
- Training throughput drops without obvious cause

**Common Causes:**

- NVLink physical connection issues
- Fabric Manager misconfiguration
- GPU topology changes
- Environmental factors (temperature, vibration)

**Detection Signals:**

- XID 74 in kernel logs
- DCGM Exporter: `DCGM_FI_DEV_NVLINK_BANDWIDTH_*` below threshold
- `nvidia-smi nvlink --status` shows inactive links
- NVLink error counters increasing

### 3. Memory Failures (内存故障)

**Symptoms:**

- XID 92, 95: GPU memory errors
- ECC errors accumulating
- Training loss divergence or NaN values
- GPU remapping events
- Application crashes with CUDA memory errors

**Common Causes:**

- Hardware memory defects
- Overheating
- Voltage instability
- Bit flips from cosmic rays (rare but possible)

**Detection Signals:**

- XID 92, 95 errors
- DCGM Exporter: `DCGM_FI_DEV_ECC_*` counters
- `nvidia-smi --query-gpu=ecc.errors.corrected.volatile.total` increasing
- GPU remapping events in NVML

### 4. Driver Failures (驱动故障)

**Symptoms:**

- NVML API calls fail or timeout
- Container runtime reports device plugin errors
- Pods stuck in `ContainerCreating` with device allocation failures
- `nvidia-smi` hangs or returns errors

**Common Causes:**

- Driver version incompatibility
- Kernel module crashes
- CUDA library mismatches
- Device plugin restarts

**Detection Signals:**

- Device plugin logs show allocation errors
- NVML API return codes indicate failure
- Container runtime errors in kubelet logs
- GPU Operator pods in `CrashLoopBackOff`

## Fault Detection Approaches

### 1. DCGM Exporter (Recommended)

NVIDIA Data Center GPU Manager (DCGM) provides comprehensive GPU telemetry and
is the industry standard for GPU monitoring in Kubernetes.

**Deployment:**

```yaml
# Deployed via NVIDIA GPU Operator
apiVersion: v1
kind: Pod
metadata:
  name: dcgm-exporter
  namespace: gpu-operator
spec:
  containers:

  - name: dcgm-exporter
    image: nvcr.io/nvidia/k8s/dcgm-exporter:3.3.8-3.6.0-ubuntu22.04
    securityContext:
      privileged: true
    volumeMounts:

    - name: pod-gpu-resources
      mountPath: /var/lib/kubelet/pod-resources
```text

**Key Metrics for Fault Detection:**

| Metric | Description | Fault Type |
| -------- | ------------- | ------------ |
| `DCGM_FI_DEV_XID_ERRORS` | XID error codes | All |
| `DCGM_FI_DEV_GPU_TEMP` | GPU temperature | Overheating |
| `DCGM_FI_DEV_POWER_VIOLATION` | Power throttling events | Power |
| `DCGM_FI_DEV_THERMAL_VIOLATION` | Thermal throttling | Cooling |
| `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` | Uncorrectable ECC errors | Memory |
| `DCGM_FI_DEV_NVLINK_BANDWIDTH_*` | NVLink bandwidth | Link |
| `DCGM_FI_DEV_NVLINK_*_REPLAY_ERROR_COUNT_*` | NVLink errors | Link |

**Prometheus Alert Example:**

```yaml
groups:

- name: gpu_health
  rules:

  - alert: GPUXidError
    expr: increase(DCGM_FI_DEV_XID_ERRORS[5m]) > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "GPU XID error detected on {{ $labels.gpu }}"
      description: "XID errors indicate serious GPU hardware issues"

  - alert: NVLinkDegraded
    expr: |
      DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL < 
      (DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL offset 1h) * 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "NVLink bandwidth degraded on {{ $labels.gpu }}"
```text

**References:**

- [DCGM Exporter GitHub](https://github.com/NVIDIA/dcgm-exporter)
- [NVIDIA Data Center Monitoring Blog](https://developer.nvidia.com/blog/making-gpu-clusters-more-efficient-with-nvidia-data-center-monitoring/)

### 2. Node Problem Detector (NPD)

Kubernetes Node Problem Detector extends monitoring to include custom GPU
health checks and integrates with Kubernetes node conditions.

**Custom GPU Plugin Example:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: node-problem-detector-config
  namespace: kube-system
data:
  gpu-health-check.sh: |
    #!/bin/bash
    # Check for XID errors in kernel log
    if dmesg | grep -q "Xid.*79\ | Xid.*74\ | Xid.*92\ | Xid.*95"; then
      echo "GPU_XID_ERROR"
      exit 1
    fi
    
    # Check nvidia-smi availability
    if ! nvidia-smi > /dev/null 2>&1; then
      echo "GPU_UNAVAILABLE"
      exit 1
    fi
    
    # Check NVLink status
    if nvidia-smi nvlink --status | grep -q "Down"; then
      echo "NVLINK_DOWN"
      exit 1
    fi
    
    exit 0

  gpu-problem-detector.json: |
    {
      "plugin": "custom",
      "pluginConfig": {
        "invoke_interval": "30s",
        "timeout": "10s",
        "max_output_length": 256,
        "concurrency": 1
      },
      "source": "gpu-health-check",
      "conditions": [
        {
          "type": "GPUHealthy",
          "reason": "GPUIsHealthy",
          "message": "GPU is functioning normally"
        }
      ],
      "rules": [
        {
          "type": "permanent",
          "condition": "GPUHealthy",
          "reason": "GPUXIDError",
          "pattern": "GPU_XID_ERROR",
          "message": "GPU XID error detected"
        },
        {
          "type": "permanent",
          "condition": "GPUHealthy",
          "reason": "GPUUnavailable",
          "pattern": "GPU_UNAVAILABLE",
          "message": "GPU unavailable via nvidia-smi"
        },
        {
          "type": "temporary",
          "condition": "GPUHealthy",
          "reason": "NVLinkDown",
          "pattern": "NVLINK_DOWN",
          "message": "NVLink connection degraded"
        }
      ]
    }
```text

**References:**

- [Node Problem Detector GitHub](https://github.com/kubernetes/node-problem-detector)
- [Azure AKS Node Problem Detector](https://learn.microsoft.com/en-us/azure/aks/node-problem-detector)

### 3. NVIDIA GPU Debug Guidelines

NVIDIA provides official debugging procedures for systematic fault diagnosis:

**XID Error Interpretation:**

- **XID 79**: GPU has fallen off the bus (card dropout)
- **XID 74**: NVLink training/initialization error
- **XID 92, 95**: Uncorrectable memory errors
- **XID 13, 31, 43**: Driver or kernel errors

**Diagnostic Flow:**

1. Identify XID error code from logs or DCGM

2. Check NVIDIA documentation for specific XID meaning

3. Verify driver version compatibility

4. Check GPU temperature and power status

5. Test GPU in isolation with stress tools

6. Consider hardware replacement if persistent

**References:**

- [NVIDIA GPU Debug Guidelines](https://docs.nvidia.com/deploy/gpu-debug-guidelines/index.html)
- [Common GPU Errors Discussion](https://www.cnblogs.com/jisongxie/p/10405302.html)

### 4. Kubernetes Native Observability

**GPU Telemetry Integration:**

- [Integrate GPU Telemetry into Kubernetes](https://cloud-atlas.readthedocs.io/zh-cn/latest/kubernetes/gpu/intergrate_gpu_telemetry_into_k8s.html)
- [DCGM Exporter Source Code Analysis](https://www.jianshu.com/p/f38e58864496)

**DRA Driver Integration:**

- NVIDIA DRA driver issues with DCGM metrics: [k8s-dra-driver-gpu #166](https://github.com/NVIDIA/k8s-dra-driver-gpu/issues/166)

## Fault Semantics and Kubernetes Integration

To enable automated remediation, GPU faults must be translated into Kubernetes-
native semantics that schedulers, controllers, and operators can act upon.

### Three-Layer Semantic Model

#### 1. NodeCondition (Node-Level)

Used when entire node GPU subsystem is compromised and should be avoided for
new workload placement.

**Standard Conditions (aligned with Azure AKS):**

```yaml
apiVersion: v1
kind: Node
metadata:
  name: gpu-node-01
status:
  conditions:

  - type: GPUHealthy
    status: "False"
    reason: GPUXIDError
    message: "XID 79 detected on GPU 0"
    lastTransitionTime: "2025-12-17T10:00:00Z"
  
  - type: NVLinkHealthy
    status: "False"
    reason: NVLinkStatusInactive
    message: "NVLink 0-1 connection down"
    lastTransitionTime: "2025-12-17T10:05:00Z"
```text

**Condition Types:**

- `GPUHealthy`: Overall GPU subsystem health
- `NVLinkHealthy`: NVLink fabric status
- `GPUDriverHealthy`: NVIDIA driver and NVML availability
- `GPUMemoryHealthy`: ECC error status within threshold

**Actions Triggered:**

- Scheduler filters: Prevent new pod placement
- Taint applied: `gpu.health/unhealthy=true:NoSchedule`
- Alert generated to operations team
- Automated remediation controller triggered

#### 2. DeviceCondition (GPU Device-Level)

Used to isolate specific faulty GPUs while keeping healthy GPUs on the same
node available for scheduling.

**Proposed CRD (for fine-grained device tracking):**

```yaml
apiVersion: gpu.nvidia.com/v1
kind: GPUDevice
metadata:
  name: gpu-node-01-gpu-0
  labels:
    node: gpu-node-01
    gpu.index: "0"
spec:
  uuid: GPU-12345678-1234-1234-1234-123456789abc
  model: NVIDIA A100-SXM4-80GB
status:
  health:
    status: Unhealthy
    reason: XIDError
    severity: Critical
    confidence: 0.95
    lastCheck: "2025-12-17T10:00:00Z"
  faults:

  - type: CardDropout
    xid: 79
    timestamp: "2025-12-17T10:00:00Z"
    count: 1
  allocatable: false
```text

**Benefits:**

- Multi-GPU nodes can continue serving with healthy GPUs
- Reduces "blast radius" of hardware failures
- Enables partial node capacity during maintenance
- Supports MIG (Multi-Instance GPU) scenarios

#### 3. WorkloadCondition (Job/Workload-Level)

Maps hardware faults to training/inference job semantics for application-aware
recovery.

**Training Job Integration:**

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata:
  name: training-job-01
status:
  conditions:

  - type: GPUFaultDetected
    status: "True"
    reason: XIDErrorOnPod
    message: "GPU fault on pod training-job-01-worker-3"
    lastTransitionTime: "2025-12-17T10:00:00Z"
  state:
    phase: Requeued
    lastTransitionTime: "2025-12-17T10:01:00Z"
    reason: GPUFaultRemediation
```text

**Integration with Training Frameworks:**

- **Volcano**: Support for job requeue on GPU failures
- **Kubeflow Training Operator**: Automatic worker replacement
- **PyTorch Elastic**: Leverage elastic training for resilience
- **Checkpointing**: Coordinate with checkpoint/restore systems

### Fault Knowledge Graph

Systematic mapping of low-level signals to actionable insights:

```text
Signal Layer:

  - XID errors (kernel logs)
  - DCGM metrics (Prometheus)
  - NVML health checks
  - NVLink status
  - PCIe AER logs
  - Fabric Manager events

↓ Signal Aggregation & Correlation ↓

Fault Attributes:

  - type: CardDropout | LinkFailure | MemoryError | DriverFailure
  - scope: device | node | fabric-domain | rack
  - severity: S0 (critical) | S1 (high) | S2 (medium) | S3 (low)
  - confidence: 0.0-1.0 (multi-signal fusion)
  - duration: transient | persistent
  - impact: workload-disrupting | performance-degrading

↓ Remediation Decision ↓

Action Hints:

  - cordon: Prevent new scheduling
  - isolate-device: Remove device from allocatable pool
  - reset-driver: Restart nvidia-fabricmanager / device-plugin
  - reset-gpu: nvidia-smi -r (high risk)
  - drain: Evict pods and reboot node
  - replace: Hardware replacement required
```text

**Example Multi-Signal Correlation:**

```text
IF (XID_79_count > 0 AND nvidia_smi_returns_error) THEN
  fault.type = CardDropout
  fault.severity = S0
  fault.confidence = 0.99
  action.hints = [cordon, drain, replace]

IF (nvlink_bandwidth < 0.8 * baseline AND XID_74_count > 3) THEN
  fault.type = LinkFailure
  fault.severity = S1
  fault.confidence = 0.85
  action.hints = [isolate-device, reset-fabricmanager]

IF (ecc_uncorrectable_errors > threshold) THEN
  fault.type = MemoryError
  fault.severity = S0
  fault.confidence = 0.90
  action.hints = [cordon, isolate-device, replace]
```text

## Progressive Remediation Strategies

The key principle: **Minimize disruption to running workloads while ensuring
cluster health**. Progress from low-impact to high-impact actions, with
verification at each step.

### Remediation Action Hierarchy

#### Level 0: Detection and Alerting (No Action)

- **Actions**: Log event, emit Prometheus alert, update NodeCondition
- **Impact**: None on workloads
- **Use case**: Monitoring, early warning
- **Rollback**: N/A

#### Level 1: Scheduling Prevention (Cordon/Taint)

- **Actions**:
  - Apply taint: `kubectl taint node gpu-node-01 gpu.health/suspect=true:NoSchedule`
  - Mark node as unschedulable
  - Emit Kubernetes Event
- **Impact**: No new pods scheduled, existing pods continue
- **Use case**: Suspected but not confirmed issues, transient faults
- **Verification**: Monitor for 5-10 minutes, check if issue persists
- **Rollback**: Remove taint, mark schedulable

#### Level 2: Soft Recovery (Service Restart)

- **Actions**:
  - Restart device plugin: `kubectl delete pod -n gpu-operator nvidia-device-plugin-xxx`
  - Restart fabric manager: `systemctl restart nvidia-fabricmanager`
  - Restart DCGM: `systemctl restart nvidia-dcgm`
- **Impact**: Brief GPU allocation pause (30-60s), running containers unaffected
- **Use case**: Driver/plugin issues, fabric manager errors
- **Verification**: Check nvidia-smi, verify device plugin readiness
- **Rollback**: N/A (service restart is idempotent)

#### Level 3: Device Isolation

- **Actions**:
  - Update device plugin config to exclude faulty GPU
  - Reduce node's allocatable GPU count
  - Mark GPUDevice CR as `allocatable: false`
- **Impact**: Reduced node capacity, running workloads on healthy GPUs continue
- **Use case**: Single GPU failure on multi-GPU node
- **Verification**: Confirm healthy GPUs still allocatable
- **Rollback**: Re-enable device in plugin config

#### Level 4: Hard Recovery (GPU Reset)

- **Actions**:
  - `nvidia-smi -r -i <gpu_id>` (requires special permissions)
  - PCI device rescan: `echo 1 > /sys/bus/pci/rescan`
- **Impact**: All containers using affected GPU are killed
- **Use case**: Persistent XID errors, GPU hangs
- **Risk**: High - can affect multiple workloads
- **Verification**: nvidia-smi shows GPU healthy, run GPU stress test
- **Rollback**: Drain and reboot if reset fails

#### Level 5: Node Drain and Reboot

- **Actions**:
  - Respect PodDisruptionBudgets
  - `kubectl drain gpu-node-01 --ignore-daemonsets --delete-emptydir-data`
  - Reboot node
  - Wait for node ready
- **Impact**: All pods on node evicted and rescheduled
- **Use case**: Driver failures, multiple GPU failures, persistent issues
- **Verification**: Node returns healthy, all GPU checks pass
- **Rollback**: Manual intervention required

#### Level 6: Node Replacement

- **Actions**:
  - Mark node for decommission
  - Drain node
  - Trigger cluster autoscaler or MCO for replacement
- **Impact**: Node removed from cluster
- **Use case**: Hardware failures requiring RMA
- **Verification**: New node healthy and joins cluster
- **Rollback**: N/A (requires hardware repair)

### Remediation Policy Engine

**Key Requirements:**

1. **Hysteresis and Cooldown**

   - Don't act on single transient signal
   - Require fault to persist for duration threshold (e.g., 5 minutes)
   - Implement cooldown between remediation attempts (e.g., 30 minutes)
   - Track remediation history to detect recurring issues

2. **Blast Radius Control**

   - Limit concurrent remediations per node pool (e.g., max 10%)
   - Limit concurrent remediations per rack/availability zone
   - Respect fabric domains (don't disrupt entire NVSwitch domain)
   - Implement rate limiting for disruptive actions

3. **Workload Awareness**

   - Different policies for training (long-running) vs inference (stateless)
   - Respect job priorities and preemption policies
   - Coordinate with checkpoint systems before eviction
   - Honor PodDisruptionBudgets strictly

4. **Verification and Rollback**

   - Post-action verification required before considering remediation successful
   - Use same detection signals to verify fix
   - Automatic rollback if verification fails
   - Exponential backoff for repeated failures

**Example Policy (Pseudocode):**

```python
def remediate_gpu_fault(node, fault):
    # Check blast radius budget
    if current_remediations_in_rack(node.rack) > MAX_RACK_REMEDIATIONS:
        return DEFER
    
    # Check fault confidence and duration
    if fault.confidence < 0.7 or fault.duration < 5min:
        return MONITOR  # Level 0
    
    # Check recent remediation history
    if node.last_remediation_time < 30min_ago:
        return DEFER  # Cooldown period
    
    # Progressive action selection
    if fault.type == "CardDropout" and fault.severity == "S0":
        # Critical fault, escalate quickly
        if not node.is_cordoned:
            action = CORDON  # Level 1
        elif not node.drain_attempted:
            action = DRAIN_AND_REBOOT  # Level 5
        else:
            action = REPLACE  # Level 6
    
    elif fault.type == "LinkFailure" and fault.severity == "S1":
        # Try soft recovery first
        if not node.fabricmanager_restarted:
            action = RESTART_FABRICMANAGER  # Level 2
        elif node.healthy_gpus > 0:
            action = ISOLATE_DEVICE  # Level 3
        else:
            action = DRAIN_AND_REBOOT  # Level 5
    
    elif fault.type == "DriverFailure":
        if not node.device_plugin_restarted:
            action = RESTART_DEVICE_PLUGIN  # Level 2
        else:
            action = DRAIN_AND_REBOOT  # Level 5
    
    # Execute action with verification
    execute_action(action, node)
    
    # Schedule post-action verification
    schedule_verification(node, action, delay=2min)
```text

### Integration with Existing Controllers

**Draino (Drain Automation):**

```yaml
# Draino watches for NodeConditions and automates drain
apiVersion: v1
kind: ConfigMap
metadata:
  name: draino-config
data:
  config.yaml: |
    conditions:

    - type: GPUHealthy
      status: "False"
      min-duration: 5m

    - type: NVLinkHealthy
      status: "False"
      min-duration: 10m
    drain-buffer: 10m
    eviction-headroom: 5
    max-concurrent-drains: 3
```text

**Node Readiness Controller:**

```yaml
# kubernetes-sigs/node-readiness-controller
apiVersion: v1
kind: ConfigMap
metadata:
  name: node-readiness-config
data:
  config.yaml: |
    maintenance_triggers:

    - node_condition:
        type: GPUHealthy
        status: "False"
      action: cordon_and_drain
      grace_period: 5m
```text

**Cluster Autoscaler:**

- Annotate unhealthy nodes for autoscaler to replace
- `cluster-autoscaler.kubernetes.io/scale-down-disabled: "true"` during
  remediation

- Coordinate with autoscaler to prevent premature scale-down

## Fault-Aware Scheduling

Extend Kubernetes scheduling to consider GPU health as a first-class dimension,
preventing workload placement on at-risk hardware.

### Scheduler Plugin Integration

**GPU Health Score Scheduler Plugin:**

```go
// Conceptual implementation
type GPUHealthScore struct {
    NodeScore float64  // 0.0 (unhealthy) to 1.0 (healthy)
    Factors   []HealthFactor
}

type HealthFactor struct {
    Name   string
    Weight float64
    Value  float64
}

func (p *GPUHealthPlugin) Score(ctx context.Context, state *framework.CycleState,
    pod *v1.Pod, nodeName string) (int64, *framework.Status) {
    
    node := p.getNode(nodeName)
    
    // Calculate health score from multiple signals
    score := 1.0
    
    // Factor 1: Recent XID errors (weight: 0.4)
    xidErrors := p.getXIDErrorCount(node, last5min)
    score *= (1.0 - 0.4 * min(xidErrors / 10.0, 1.0))
    
    // Factor 2: NVLink health (weight: 0.3)
    nvlinkHealth := p.getNVLinkBandwidth(node) / p.getBaselineNVLinkBandwidth(node)
    score *= (0.7 + 0.3 * nvlinkHealth)
    
    // Factor 3: ECC errors (weight: 0.2)
    eccErrors := p.getECCUncorrectableErrors(node, last1hour)
    score *= (1.0 - 0.2 * min(eccErrors / 100.0, 1.0))
    
    // Factor 4: Temperature (weight: 0.1)
    temp := p.getGPUTemperature(node)
    if temp > 85 {
        score *= (1.0 - 0.1 * (temp - 85) / 15.0)
    }
    
    // Convert to scheduler score (0-100)
    return int64(score * 100), nil
}
```text

**Filter Plugin for Minimum Health Threshold:**

```go
func (p *GPUHealthPlugin) Filter(ctx context.Context, state *framework.CycleState,
    pod *v1.Pod, nodeInfo *framework.NodeInfo) *framework.Status {
    
    // Check if pod requires high GPU health
    minHealthAnnotation := pod.Annotations["gpu.health/min-score"]
    if minHealthAnnotation == "" {
        return nil  // No requirement
    }
    
    minHealth, _ := strconv.ParseFloat(minHealthAnnotation, 64)
    nodeHealth := p.getNodeHealthScore(nodeInfo.Node())
    
    if nodeHealth < minHealth {
        return framework.NewStatus(framework.Unschedulable,
            fmt.Sprintf("Node GPU health %.2f below required %.2f",
                nodeHealth, minHealth))
    }
    
    return nil
}
```text

### Kueue/Volcano Integration

**Kueue Queue with Health Requirements:**

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: training-high-priority
spec:
  cohort: default
  resourceGroups:

  - coveredResources: ["gpu"]
    flavors:

    - name: a100-healthy
      resources:

      - name: gpu
        nominalQuota: 32
      # Custom label selector for healthy nodes
      nodeSelector:
        gpu.health/score: "0.9"  # Only use nodes with >0.9 health

    - name: a100-standard
      resources:

      - name: gpu
        nominalQuota: 64
      nodeSelector:
        gpu.health/score: "0.7"  # Lower bar for standard workloads
```text

**Volcano Gang Scheduling with Health:**

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata:
  name: distributed-training
spec:
  minAvailable: 4
  schedulerName: volcano
  plugins:
    healthaware: []  # Custom plugin
  tasks:

  - replicas: 4
    template:
      metadata:
        annotations:
          gpu.health/min-score: "0.8"  # Require 0.8+ health
      spec:
        containers:

        - name: worker
          resources:
            limits:
              nvidia.com/gpu: 8
```text

### DRA Health Integration

With Dynamic Resource Allocation (DRA), GPU health can influence claim
allocation and device selection:

```yaml
apiVersion: resource.k8s.io/v1alpha3
kind: ResourceClaim
metadata:
  name: training-gpus
spec:
  devices:
    requests:

    - name: gpus
      deviceClassName: gpu.nvidia.com
      count: 8
      selectors:

      - cel:
          expression: |
            device.health.score > 0.9 &&
            device.health.xidErrors == 0 &&
            device.health.nvlinkStatus == "active"
```text

**DRA Driver Health Extension:**

```go
// Extend NVIDIA DRA driver to expose health attributes
type GPUDevice struct {
    UUID  string
    Model string
    Health struct {
        Score        float64
        XIDErrors    int64
        NVLinkStatus string
        ECCErrors    int64
        LastCheck    time.Time
    }
}

// Driver populates health during discovery
func (d *driver) GetDevices() []*GPUDevice {
    devices := d.discoverGPUs()
    for _, device := range devices {
        device.Health = d.checkDeviceHealth(device.UUID)
    }
    return devices
}
```text

## Job-Level Attribution and Billing

Understanding which workloads trigger GPU faults is critical for:

- Fair resource accounting and chargeback
- Identifying problematic applications
- Capacity planning and hardware refresh decisions
- SLA enforcement

### DCGM HPC Job Mapping

DCGM Exporter supports mapping GPU metrics to specific jobs/pods using the
HPC job mapping feature.

**GPU Operator Configuration (v25.10.1+):**

```yaml
apiVersion: nvidia.com/v1
kind: ClusterPolicy
metadata:
  name: cluster-policy
spec:
  dcgmExporter:
    enabled: true
    hpcJobMapping:
      enabled: true
      directory: /var/lib/kubelet/pod-resources
      volumeMount:
        hostPath: /var/lib/kubelet/pod-resources
        mountPath: /var/lib/kubelet/pod-resources
```text

**Job Mapping File Format:**

```text
# Generated by job-mapping controller
# Format: <GPU UUID>,<Job ID>,<Job Name>,<Job User>,<Job Start Time>
GPU-12345678-1234-1234-1234-123456789abc,job-12345,training-job-01,team-ml,1702800000
GPU-87654321-4321-4321-4321-cba987654321,job-12346,inference-serve,team-ai,1702800060
```text

**Enhanced DCGM Metrics with Job Labels:**

```text
# Without job mapping
DCGM_FI_DEV_GPU_UTIL{gpu="0",UUID="GPU-12345...",modelName="A100-SXM4-80GB"} 95.0

# With job mapping
DCGM_FI_DEV_GPU_UTIL{
  gpu="0",
  UUID="GPU-12345...",
  modelName="A100-SXM4-80GB",
  job_id="job-12345",
  job_name="training-job-01",
  namespace="ml-team",
  pod="training-job-01-worker-0"
} 95.0
```text

### Kubernetes Job Mapping Controller

DCGM's HPC job mapping was designed for HPC schedulers (Slurm, PBS). For
Kubernetes, we need a controller to generate mapping files:

**Controller Responsibilities:**

1. Watch Pod creation/deletion events

2. Query kubelet pod-resources API to get GPU assignments

3. Generate DCGM-compatible mapping files

4. Update mappings on pod GPU allocation changes

5. Clean up mappings when pods terminate

**Example Implementation:**

```go
type JobMappingController struct {
    kubeclient kubernetes.Interface
    podResourcesClient podresourcesapi.PodResourcesListerClient
    mappingDir string
}

func (c *JobMappingController) reconcilePod(pod *v1.Pod) error {
    // Get GPU allocations for this pod
    resp, err := c.podResourcesClient.List(context.TODO(), &podresourcesapi.ListPodResourcesRequest{})
    if err != nil {
        return err
    }
    
    var mappings []string
    for _, podRes := range resp.PodResources {
        if podRes.Namespace != pod.Namespace | |  podRes.Name != pod.Name {
            continue
        }
        
        for _, container := range podRes.Containers {
            for _, device := range container.Devices {
                if device.ResourceName == "nvidia.com/gpu" {
                    for _, deviceID := range device.DeviceIds {
                        uuid := c.getGPUUUID(deviceID)
                        jobID := string(pod.UID)
                        jobName := fmt.Sprintf("%s/%s", pod.Namespace, pod.Name)
                        jobUser := pod.Labels["workload.user"]
                        startTime := pod.CreationTimestamp.Unix()
                        
                        mapping := fmt.Sprintf("%s,%s,%s,%s,%d",
                            uuid, jobID, jobName, jobUser, startTime)
                        mappings = append(mappings, mapping)
                    }
                }
            }
        }
    }
    
    // Write to mapping file
    mappingFile := filepath.Join(c.mappingDir, fmt.Sprintf("pod-%s.txt", pod.UID))
    return os.WriteFile(mappingFile, []byte(strings.Join(mappings, "\n")), 0644)
}
```text

### Fault Attribution Queries

With job-aware metrics, we can attribute faults to specific workloads:

**Query: Which job triggered XID errors?**

```promql
increase(DCGM_FI_DEV_XID_ERRORS{job_name!=""}[1h]) > 0
```text

**Query: GPU utilization when fault occurred:**

```promql
DCGM_FI_DEV_GPU_UTIL{job_name="training-job-01"}
  and on(gpu, UUID)
  increase(DCGM_FI_DEV_XID_ERRORS[5m]) > 0
```text

**Query: Cost attribution for GPU downtime:**

```promql
sum by (namespace, job_name) (
  rate(DCGM_FI_DEV_GPU_UTIL[1h]) *
  (1 - (increase(DCGM_FI_DEV_XID_ERRORS[1h]) > bool 0))
) * GPU_HOURLY_COST
```text

### Chargeback and SLA Enforcement

**Fair Billing Adjustment:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gpu-billing-policy
data:
  policy.yaml: |
    # Don't charge users for time when GPU was unhealthy
    # due to hardware (not user-caused) failures
    fault_types:
      hardware_failure:
        charge_adjustment: 0.0  # No charge
        xids: [79, 74]  # Card dropout, NVLink failure
      
      user_oom:
        charge_adjustment: 1.0  # Full charge
        xids: [13, 31]  # Out of memory, driver error
      
      memory_error:
        charge_adjustment: 0.5  # Shared responsibility
        xids: [92, 95]  # ECC errors (could be workload stress)
```text

## Production Implementation

### Reference Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Detection Layer                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • DCGM Exporter (GPU metrics)                           │  │
│  │  • Node Problem Detector (System checks)                 │  │
│  │  • Kernel Log Monitoring (XID errors)                    │  │
│  │  • NVML Health Checks                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Correlation & Semantics                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • Prometheus Rules (Alert aggregation)                  │  │
│  │  • Fault Classification (XID→Fault Type)                 │  │
│  │  • Confidence Scoring (Multi-signal fusion)              │  │
│  │  • NodeCondition/DeviceCondition Updates                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Remediation Controller                    │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • Policy Engine (Blast radius, workload awareness)      │  │
│  │  • Action Executor (Cordon/Drain/Reset/Replace)          │  │
│  │  • Verification Loop (Post-action health check)          │  │
│  │  • Integration: Draino, Node Readiness Controller        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Fault-Aware Scheduling                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • Scheduler Plugin (Health scoring)                     │  │
│  │  • Kueue/Volcano (Queue-level health requirements)       │  │
│  │  • DRA Driver (Device-level health attributes)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                Job Attribution & Billing                  │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • Job Mapping Controller (Pod→GPU mapping)              │  │
│  │  • DCGM HPC Job Mapping (Metrics enrichment)             │  │
│  │  • Billing Adjustment (Fault-aware chargeback)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```text

### Deployment Checklist

**Phase 1: Detection (MVP)**
- [ ] Deploy NVIDIA GPU Operator with DCGM Exporter
- [ ] Configure Prometheus to scrape DCGM metrics
- [ ] Create Prometheus alerts for critical XID errors
- [ ] Deploy Node Problem Detector with GPU health checks
- [ ] Set up monitoring dashboards (Grafana)

**Phase 2: Basic Remediation**
- [ ] Deploy Draino for automated node drain on conditions
- [ ] Configure Node Readiness Controller
- [ ] Implement manual runbooks for GPU reset/reboot
- [ ] Set up incident response procedures
- [ ] Define blast radius limits per rack/AZ

**Phase 3: Advanced Remediation**
- [ ] Implement device-level isolation (GPUDevice CRD)
- [ ] Deploy remediation controller with progressive policies
- [ ] Add verification loops for all remediation actions
- [ ] Implement cooldown and rate limiting
- [ ] Add workload-aware policies (training vs inference)

**Phase 4: Fault-Aware Scheduling**
- [ ] Implement GPU health scoring scheduler plugin
- [ ] Integrate health requirements into Kueue/Volcano
- [ ] Extend DRA driver with health attributes
- [ ] Add admission policies for critical workloads
- [ ] Implement health-based autoscaling policies

**Phase 5: Attribution and Optimization**
- [ ] Deploy job mapping controller
- [ ] Enable DCGM HPC job mapping
- [ ] Implement fault attribution queries
- [ ] Set up chargeback adjustment policies
- [ ] Create capacity planning reports

### Best Practices

**1. Start Conservative**
- Begin with detection and alerting only (no automation)
- Gradually enable automation with strict rate limits
- Validate detection accuracy before enabling remediation
- Keep humans in the loop for critical decisions

**2. Measure and Iterate**
- Track false positive rate for fault detection
- Measure MTTR (Mean Time To Recovery) improvements
- Monitor "collateral damage" from remediation actions
- Collect feedback from workload owners

**3. Security and Compliance**
- Audit all automated remediation actions
- Require approval for destructive actions (GPU reset, reboot)
- Use RBAC to limit remediation controller permissions
- Implement change notifications via webhooks/Slack

**4. Integration Points**
- Coordinate with cluster autoscaler for node replacement
- Integrate with incident management systems (PagerDuty, OpsGenie)
- Feed data to capacity planning tools
- Sync with hardware maintenance schedules

## References

### Industry Implementations

**ByteDance Volcano:**

- [GPU Fault Detection and Self-Healing (Chinese)](https://mp.weixin.qq.com/s/vc4y2wnZlyou3cfqnQP2-w)
- Comprehensive approach to GPU health monitoring and automated recovery

**Microsoft Azure AKS:**

- [Node Problem Detector](https://learn.microsoft.com/en-us/azure/aks/node-problem-detector)
- Standardized GPU condition types: `GPUMissing`, `NVLinkStatusInactive`,
  `XIDErrors`, `IBLinkFlapping`

**NVIDIA Resources:**

- [DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter)
- [GPU Debug Guidelines](https://docs.nvidia.com/deploy/gpu-debug-guidelines/index.html)
- [GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [Data Center Monitoring Blog](https://developer.nvidia.com/blog/making-gpu-clusters-more-efficient-with-nvidia-data-center-monitoring/)
- [k8s-dra-driver-gpu](https://github.com/NVIDIA/k8s-dra-driver-gpu)

### Community Resources

**Kubernetes:**

- [Node Problem Detector](https://github.com/kubernetes/node-problem-detector)
- [Node Readiness Controller](https://github.com/kubernetes-sigs/node-readiness-controller)
- [Dynamic Resource Allocation (DRA)](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)
- [WG Batch](https://github.com/kubernetes/community/blob/master/wg-batch/README.md)
- [WG Device Management](https://github.com/kubernetes/community/blob/master/wg-device-management/README.md)

**Automation:**

- [Draino](https://github.com/planetlabs/draino) - Automated node drain

**Case Studies:**

- [GPU Fault Investigation Story (Chinese)](https://mp.weixin.qq.com/s/ehcX_43lmpaYaQS_x49BcA)
- [GPU Troubleshooting on Kubernetes (Chinese)](https://nolebase.ayaka.io/zh-CN/%E7%AC%94%E8%AE%B0/%F0%9F%A7%B1%20%E5%9F%BA%E7%A1%80%E8%AE%BE%E6%96%BD/%F0%9F%9A%A2%20Kubernetes/%E5%9C%A8%20Kubernetes%20%E9%9B%86%E7%BE%A4%E4%B8%8A%E7%9A%84%20GPU%20%E6%8E%89%E5%8D%A1%E5%92%8C%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5.html)
- [GPU Disappearance Troubleshooting (Chinese)](https://www.cnblogs.com/jisongxie/p/10405302.html)
- [Kubernetes GPU Telemetry Integration (Chinese)](https://cloud-atlas.readthedocs.io/zh-cn/latest/kubernetes/gpu/intergrate_gpu_telemetry_into_k8s.html)
- [DCGM Exporter Source Analysis (Chinese)](https://www.jianshu.com/p/f38e58864496)

### Related Documentation

- [NVIDIA GPU Operator](./nvidia-gpu-operator.md)
- [Dynamic Resource Allocation (DRA)](./dra.md)
- [Observability Guide](../observability/README.md)
- [Training Fault Tolerance](../training/README.md)

---

**Warning:** Some content in this guide references AI-generated summaries and
community discussions. Always validate approaches in your specific environment
and consult official NVIDIA documentation for hardware-specific guidance.
