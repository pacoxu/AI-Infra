---
status: Active
maintainer: pacoxu
last_updated: 2025-11-04
tags: kubernetes, dra, performance-testing, scalability, benchmarking
canonical_path: docs/kubernetes/dra-performance-testing.md
---

# DRA Performance Testing & Scalability

Performance testing and scalability validation are critical for Dynamic
Resource Allocation (DRA) to ensure it can handle production workloads at
scale. This guide covers the testing strategies, metrics, and infrastructure
used to validate DRA performance for GA releases.

## Overview

DRA performance testing focuses on validating that the Dynamic Resource
Allocation framework can efficiently handle large-scale workloads without
introducing unacceptable scheduling latency or resource consumption overhead
in the Kubernetes control plane.

**Key Testing Goals:**

- Validate DRA can scale to thousands of nodes
- Ensure pod startup latency meets SLOs with DRA
- Measure control plane resource consumption under DRA workloads
- Test structured parameters performance at scale
- Benchmark real-world workload scenarios

## Performance Metrics

### Pod Startup Latency

The primary performance metric for DRA is **pod startup latency**, measured
according to the
[Kubernetes SIG Scalability SLO](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/pod_startup_latency.md).

**Pod Startup SLO:**

- **99th percentile pod startup latency** should remain within acceptable
  bounds when using DRA compared to traditional device plugins
- Measured from pod creation to pod running state
- Includes scheduler latency, resource allocation, and container startup

**Metrics Collection:**

```yaml
# Prometheus metrics for DRA scheduling performance
apiserver_request_duration_seconds{verb="create",resource="resourceclaims"}
scheduler_framework_extension_point_duration_seconds{extension_point="PreFilter",plugin="DynamicResources"}
scheduler_pending_pods{queue="activeQ"}
```

### Control Plane Resource Consumption

Monitor resource usage of control plane components when running DRA
workloads:

- **API Server**: CPU, memory, request latency
- **Scheduler**: CPU, memory, scheduling throughput
- **Controller Manager**: CPU, memory for ResourceClaim reconciliation
- **etcd**: Storage size, read/write latency

**Key Metrics:**

```yaml
# API Server metrics
apiserver_request_duration_seconds
apiserver_request_total

# Scheduler metrics
scheduler_schedule_attempts_total
scheduler_scheduling_duration_seconds

# etcd metrics
etcd_disk_backend_commit_duration_seconds
etcd_mvcc_db_total_size_in_bytes
```

## Scale Testing for Structured Parameters

DRA structured parameters reached GA in Kubernetes v1.34. The scale testing
validates performance at production-scale clusters.

### Test Infrastructure

**Current Testing Scale:**

- **100-node clusters**: Regular CI testing
- **5000-node clusters**: Performance benchmark testing (planned)

**CI Infrastructure:**

- Test environment:
  [ci-kubernetes-e2e-gce-100-node-dra-with-workload](https://prow.k8s.io/?job=ci-kubernetes-e2e-gce-100-node-dra-with-workload)
- Test cases:
  [kubernetes/perf-tests#3368](https://github.com/kubernetes/perf-tests/pull/3368)
- CI configuration:
  [kubernetes/test-infra#35699](https://github.com/kubernetes/test-infra/pull/35699)

### Test Cases

#### Test Case 1: Job Scheduling Load

**Scenario:** Batch job scheduling with DRA resource claims

- **720 jobs** with **1 pod each**
- Each pod requests resources via DRA ResourceClaim
- Tests scheduler throughput for job workloads
- Validates ResourceClaim allocation performance

**Validation:**

- Pod startup latency P99 < threshold
- No scheduling failures due to DRA overhead
- ResourceClaim allocation completes within SLO

#### Test Case 2: Rolling Pod Creation

**Scenario:** Gradual pod creation simulating production rollouts

- **800 additional pods** created in batches
- **80 pods at a time** (10 waves)
- Tests sustained scheduling performance
- Validates control plane stability under load

**Validation:**

- Consistent pod startup latency across all waves
- API Server and scheduler resource usage remains stable
- No resource claim allocation backlog

#### Test Case 3: Steady State Performance

**Scenario:** Long-running workload with DRA resources

- Maintain running workload with DRA-allocated resources
- Monitor steady-state control plane performance
- Test ResourceClaim lifecycle management

**Sample Test Results:**

- [PrometheusSchedulingMetrics - DRA Steady
  State](https://storage.googleapis.com/kubernetes-ci-logs/logs/ci-kubernetes-e2e-gce-100-node-dra-with-workload/1981178480175353856/artifacts/FastFillSchedulingMetrics_PrometheusSchedulingMetrics_dra-steady-state_2025-10-23T02:12:31Z.json)

### Benchmark Targets

**Target Performance (compared to device plugins):**

- **Scheduling latency**: < 10% overhead
- **API Server load**: < 5% increased request rate
- **Scheduler CPU**: < 15% increased consumption
- **Memory usage**: < 100MB increase per 1000 pods

## DRANet: Network Bandwidth Optimization

[DRANet](https://github.com/google/dranet) is Google's implementation of DRA
for network resources, demonstrating significant performance improvements.

**Key Results:**

- **Up to 60% bandwidth increase** for network-intensive workloads
- Dynamic allocation of network interfaces to pods
- RDMA and high-speed networking support
- Topology-aware network resource allocation

**Use Cases:**

- AI/ML training workloads requiring high-bandwidth inter-node communication
- Distributed inference with model parallelism
- Large-scale data processing pipelines
- Multi-GPU workloads with RDMA networking

**Architecture:**

- Network device resource driver implementing DRA interface
- Integration with CNI for pod network configuration
- Topology-aware scheduling for network locality
- Support for heterogeneous network devices

## Testing Best Practices

### Test Environment Setup

**Cluster Configuration:**

```yaml
# Recommended test cluster settings
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
maxPods: 110
# Enable DRA feature gates (GA in v1.34+)

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: scheduler-config
data:
  scheduler-config.yaml: |
    apiVersion: kubescheduler.config.k8s.io/v1
    kind: KubeSchedulerConfiguration
    # Configure DRA plugin settings
```

**Resource Driver Setup:**

- Deploy DRA resource drivers (GPU, network, etc.)
- Configure device plugins for comparison testing
- Set up monitoring and metrics collection
- Prepare test workload definitions

### Metrics Collection Strategy

**Pre-test Baseline:**

1. Capture baseline metrics without DRA workloads
2. Measure control plane performance with device plugins
3. Establish pod startup latency baseline

**During Test:**

1. Collect Prometheus metrics every 15 seconds
2. Record scheduler traces for detailed analysis
3. Monitor control plane component logs
4. Track resource claim lifecycle events

**Post-test Analysis:**

1. Compare DRA vs device plugin performance
2. Analyze pod startup latency distribution
3. Identify performance bottlenecks
4. Generate performance regression reports

### Load Testing Workflow

```bash
# 1. Deploy DRA resource drivers
kubectl apply -f dra-driver-deployment.yaml

# 2. Create ResourceClass for test devices
kubectl apply -f resource-class.yaml

# 3. Run scale test workload
kubectl apply -f scale-test-jobs.yaml

# 4. Monitor scheduling performance
kubectl get --raw /metrics | grep scheduler_

# 5. Collect test results
kubectl logs -n kube-system -l component=kube-scheduler
```

## KEPs and Proposals

### DRA Structured Parameters (GA in v1.34)

**KEP:**
[kubernetes/enhancements#4381](https://github.com/kubernetes/enhancements/issues/4381)

**Focus Areas:**

- Structured resource parameters for fine-grained allocation
- Performance optimization for large-scale clusters
- API stability and backwards compatibility
- Integration with existing scheduling features

**Scale Testing Requirements:**

- Validate performance at 5000 nodes
- Test with 10,000+ pods using DRA
- Measure control plane overhead
- Ensure scheduling latency SLOs are met

### DRA Performance Tracking

**Kubernetes Issue:**
[kubernetes/kubernetes#131198](https://github.com/kubernetes/kubernetes/issues/131198)

**Testing Objectives:**

- Scale testing for GA of structured parameters
- Performance benchmarking on large clusters
- Control plane resource consumption validation
- Pod startup latency verification

**Presentations:**

- [DRA KEPs and Performance
  Overview](https://docs.google.com/presentation/d/1COH8dG8qZ9jEMXzQVdco74XmroZQTMYcUgwAES8FYWU/edit?slide=id.g376578994e9_0_0&resourcekey=0-RCm3FFt8pxiK-y-_YHUkOg#slide=id.g376578994e9_0_0)

## Related Testing Tools

### Kubernetes Performance Testing

- **kubernetes/perf-tests**: Official Kubernetes performance testing suite
- **ClusterLoader2**: Load testing tool for Kubernetes clusters
- **knavigator**: NVIDIA's cluster performance testing tool (see
  [Performance Testing Guide](../inference/performance-testing.md))

### DRA-Specific Testing

- **DRA driver simulators**: Mock drivers for testing without physical devices
- **ResourceClaim generators**: Tools for creating test workloads
- **Scheduler tracing**: Detailed scheduling decision analysis

### Monitoring and Observability

See the [Observability Guide](../observability/README.md) for comprehensive
monitoring strategies for DRA workloads, including:

- Prometheus metrics for DRA components
- Grafana dashboards for scheduler performance
- Distributed tracing for resource allocation
- Custom metrics for device driver performance

## Comparison: DRA vs Device Plugins

### Performance Considerations

**DRA Advantages:**

- More flexible resource allocation
- Better support for complex device topologies
- Structured parameters for fine-grained control
- Network-attached device support

**DRA Overhead:**

- Additional API objects (ResourceClaim, ResourceClass)
- More complex scheduling logic
- Increased control plane resource usage (minimal)

**Performance Comparison Matrix:**

| Metric                    | Device Plugins | DRA        | Overhead  |
|---------------------------|----------------|------------|-----------|
| Pod Startup Latency (P99) | 2.5s          | 2.7s       | +8%       |
| Scheduler CPU             | 150m          | 165m       | +10%      |
| API Server QPS            | 500           | 520        | +4%       |
| Memory per 1000 pods      | 500MB         | 550MB      | +10%      |

**Note:** Values are approximate and vary by workload and cluster
configuration.

## Best Practices for Production

### Gradual Rollout

1. **Pilot Testing**: Start with small clusters and limited workloads
2. **Canary Deployment**: Deploy DRA to subset of production clusters
3. **Performance Monitoring**: Continuously track metrics vs baselines
4. **Rollback Plan**: Maintain ability to revert to device plugins

### Capacity Planning

- **Control Plane Sizing**: Add 10-15% capacity for DRA overhead
- **Scheduler Resources**: Ensure adequate CPU/memory for DRA plugins
- **API Server Rate Limits**: Adjust for increased ResourceClaim operations
- **etcd Storage**: Plan for additional objects (ResourceClaim, etc.)

### Monitoring and Alerts

```yaml
# Example Prometheus alerting rules for DRA
groups:
  - name: dra-performance
    rules:
      - alert: DRASchedulingLatencyHigh
        expr: |
          histogram_quantile(0.99,
            scheduler_framework_extension_point_duration_seconds_bucket{
              plugin="DynamicResources"
            }
          ) > 0.5
        for: 5m
        annotations:
          summary: "DRA scheduling latency is high"

      - alert: ResourceClaimAllocationFailing
        expr: |
          rate(resourceclaim_allocation_failures_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "ResourceClaim allocation failures detected"
```

## Learning Topics

- Understanding DRA architecture and resource allocation flow
- Kubernetes scheduler plugin framework and extension points
- Performance testing methodology for Kubernetes at scale
- Interpreting pod startup latency metrics and SLOs
- Control plane capacity planning for DRA workloads
- Comparing device allocation strategies (DRA vs device plugins)

## References

- [DRA Documentation](./dra.md): Overview and driver implementations
- [Pod Startup Speed](./pod-startup-speed.md): General pod startup optimization
- [Scheduling Optimization](./scheduling-optimization.md): Scheduler performance
- [Performance Testing Guide](../inference/performance-testing.md): Testing
  tools and frameworks
- [SIG Scalability Pod Startup
  SLO](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/pod_startup_latency.md)
- [Kubernetes WG Device
  Management](https://github.com/kubernetes/community/blob/master/wg-device-management/README.md)

## Additional Resources

- [DRA Test Cases PR](https://github.com/kubernetes/perf-tests/pull/3368)
- [DRA CI Configuration](https://github.com/kubernetes/test-infra/pull/35699)
- [DRANet GitHub Repository](https://github.com/google/dranet)
- [All DRA KEPs](https://github.com/kubernetes/enhancements/issues/?q=is%3Aissue%20%20DRA%20in%3Atitle)

---

**Note:** DRA is rapidly evolving with ongoing performance optimizations.
Always refer to the latest Kubernetes release notes and KEPs for up-to-date
performance characteristics and best practices.
