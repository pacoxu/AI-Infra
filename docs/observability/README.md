---
status: Active
maintainer: pacoxu
last_updated: 2025-11-04
tags: observability, monitoring, metrics, gpu, llm, inference
canonical_path: docs/observability/README.md
---

# Observability of AI Workloads

Observability is critical for operating AI workloads at scale. This guide
covers monitoring, metrics, and observability tools across the AI
infrastructure stack: from GPU hardware to inference performance to scheduler
efficiency.

## Overview

AI workload observability spans multiple layers:

1. **Infrastructure Layer**: GPU utilization, memory, temperature, power
2. **Inference Layer**: Request latency, throughput, token metrics
3. **Scheduler Layer**: Queue depth, scheduling latency, resource allocation
4. **Application Layer**: LLM request traces, prompt performance, model quality

## Infrastructure-Side Observability

### GPU Monitoring

Track hardware-level metrics for GPU health and utilization:

**Key Metrics:**

- **GPU Utilization**: Percentage of time GPU is actively computing
- **GPU Memory**: Allocated vs. available memory per GPU
- **Temperature**: Operating temperature and thermal throttling
- **Power Consumption**: Watts used per GPU and total cluster power
- **SM Occupancy**: Streaming Multiprocessor utilization
- **NVLink/PCIe Bandwidth**: Inter-GPU and CPU-GPU communication speed

**Tools and Projects:**

- <a href="https://github.com/NVIDIA/dcgm-exporter">`NVIDIA DCGM
  Exporter`</a>: Prometheus exporter for NVIDIA Data Center GPU Manager
  metrics. Industry standard for GPU monitoring in Kubernetes.
- <a href="https://github.com/NVIDIA/gpu-operator">`NVIDIA GPU
  Operator`</a>: Kubernetes operator that deploys DCGM and monitoring stack
  automatically. See [NVIDIA GPU Operator](../kubernetes/nvidia-gpu-operator.md)
  for details.
- <a href="https://github.com/kubernetes-sigs/metrics-server">`Metrics
  Server`</a>: Kubernetes SIG project for resource metrics (CPU, memory, GPU).
- <a href="https://github.com/prometheus/prometheus">`Prometheus`</a>: CNCF
  Graduated. Time-series database for metrics collection and alerting.
- <a href="https://github.com/grafana/grafana">`Grafana`</a>: CNCF Incubating.
  Visualization and dashboarding for GPU and infrastructure metrics.

**Example Queries:**

```promql
# GPU utilization across cluster
avg(DCGM_FI_DEV_GPU_UTIL) by (gpu, kubernetes_node)

# GPU memory usage percentage
(DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE)) * 100

# GPUs with high temperature
DCGM_FI_DEV_GPU_TEMP > 80
```

### Node and Cluster Metrics

Beyond GPUs, monitor compute, network, and storage resources:

- **CPU/Memory**: Node-level resource utilization
- **Network**: Bandwidth, packet loss, RDMA metrics
- **Storage**: I/O throughput, latency for model loading and checkpointing
- **NUMA**: Non-uniform memory access patterns affecting GPU performance

## Inference-Side Observability

### Key Inference Metrics

LLM inference performance is measured by several critical metrics:

**Latency Metrics:**

- **TTFT (Time to First Token)**: Time from request submission to first token
  generated. Critical for user experience in interactive applications.
  Target: < 200ms for real-time chat.
- **TPOT (Time Per Output Token)**: Time to generate each subsequent token
  after the first. Impacts streaming speed. Target: < 50ms for smooth
  streaming.
- **ITL (Inter-Token Latency)**: Variation in time between consecutive tokens.
  Low ITL provides consistent streaming experience.
- **E2E Latency**: Total request latency from submission to completion.

**Throughput Metrics:**

- **Tokens Per Second (TPS)**: Total tokens generated per second across all
  requests.
- **Requests Per Second (RPS)**: Number of inference requests completed per
  second.
- **Batch Size**: Number of requests processed together (higher = better GPU
  utilization).

**Resource Metrics:**

- **KV Cache Utilization**: Memory used for key-value cache in transformer
  models.
- **Decode Efficiency**: Ratio of compute time to token generation time.
- **GPU Compute Utilization**: Percentage of GPU actively performing inference.

**Quality Metrics:**

- **Token Accuracy**: For speculative decoding and draft models.
- **Cache Hit Rate**: For prefix caching and prompt caching strategies.

### Inference Observability Tools

**OpenTelemetry-Native Solutions:**

- <a href="https://github.com/openlit/openlit">`OpenLit`</a>: Open source
  platform for AI Engineering with OpenTelemetry-native LLM observability.
  Provides metrics, traces, and logs for GenAI applications.
- <a href="https://github.com/traceloop/openllmetry">`OpenLLMetry`</a>: Open
  source observability for GenAI and LLM applications based on OpenTelemetry.
  One-line integration with popular LLM frameworks.

**LLM-Specific Platforms:**

- <a href="https://github.com/langfuse/langfuse">`Langfuse`</a>: Open source
  LLM engineering platform providing observability, metrics, evaluations, and
  prompt management. Supports tracing complex LLM chains and agent workflows.
- <a href="https://github.com/truera/trulens">`TruLens`</a>: Evaluation and
  tracking for LLM experiments and AI agents. Provides feedback functions for
  quality assessment.

**Model Validation and Testing:**

- <a href="https://github.com/deepchecks/deepchecks">`Deepchecks`</a>: Tests
  for continuous validation of ML models and data. Includes drift detection
  and model performance monitoring.

**Network and Distributed Tracing:**

- <a href="https://github.com/deepflowio/deepflow">`DeepFlow`</a>:
  Observability platform with deep network visibility. Supports tracing across
  distributed AI workloads and microservices.
- <a href="https://github.com/okahu">`Okahu`</a>: Organization focused on
  observability and optimization for AI infrastructure.

### Inference Platform Integration

Most LLM inference platforms provide built-in observability:

**vLLM Metrics:**

```python
# vLLM exposes Prometheus metrics at /metrics endpoint
- vllm:prompt_tokens_total
- vllm:generation_tokens_total
- vllm:time_to_first_token_seconds
- vllm:time_per_output_token_seconds
- vllm:num_requests_running
- vllm:gpu_cache_usage_perc
```

**Ray Serve (for distributed inference):**

```python
# Ray dashboard provides detailed metrics
- ray_serve_replica_processing_latency_ms
- ray_serve_num_router_requests
- ray_serve_deployment_queued_queries
```

**Triton Inference Server:**

```bash
# Triton metrics endpoint
curl http://localhost:8002/metrics

# Key metrics
nv_inference_request_success
nv_inference_request_duration_us
nv_inference_queue_duration_us
nv_gpu_utilization
```

## Scheduler-Side Observability

### Kubernetes Scheduler Metrics

Monitor scheduling efficiency and resource allocation:

**Key Metrics:**

- **Scheduling Latency**: Time from pod creation to scheduling decision
- **Scheduling Attempts**: Number of attempts before successful scheduling
- **Pending Pods**: Pods waiting for scheduling, by reason
- **Preemption Events**: Lower-priority pods evicted for higher-priority ones
- **Queue Depth**: Jobs waiting in batch scheduling queues

**Kubernetes Native Metrics:**

```promql
# Scheduling latency by operation
histogram_quantile(0.99,
  sum(rate(scheduler_scheduling_duration_seconds_bucket[5m]))
  by (le, operation))

# Pending pods by reason
sum(kube_pod_status_phase{phase="Pending"}) by (reason)

# Failed scheduling attempts
rate(scheduler_schedule_attempts_total{result="error"}[5m])
```

**Batch Scheduler Observability:**

- <a href="https://github.com/kubernetes-sigs/kueue">`Kueue`</a>: Job queuing
  for Kubernetes with queue depth metrics, admission latency, and resource
  quota utilization.
- <a href="https://github.com/volcano-sh/volcano">`Volcano`</a>: Batch
  scheduler with gang scheduling metrics, job lifecycle tracking, and queue
  management.
- <a href="https://github.com/koordinator-sh/koordinator">`Koordinator`</a>:
  QoS-based scheduling with fine-grained resource metrics and colocation
  efficiency.

### GPU Scheduling Metrics

Specialized metrics for GPU workload scheduling:

- **GPU Allocation Time**: Time to find and allocate GPU resources
- **GPU Fragmentation**: Wasted GPU capacity due to allocation patterns
- **Multi-GPU Job Scheduling**: Latency for jobs requiring multiple GPUs
- **GPU Utilization Post-Scheduling**: Actual vs. requested GPU usage

**Tools:**

- <a href="https://github.com/Project-HAMi/HAMi">`HAMi`</a>: Heterogeneous AI
  Computing Virtualization Middleware with GPU sharing metrics
- <a href="https://github.com/NVIDIA/k8s-device-plugin">`NVIDIA Device
  Plugin`</a>: GPU allocation tracking in Kubernetes

## Best Practices

### 1. Instrumentation Strategy

- **Start with infrastructure metrics**: GPU, CPU, memory, network
- **Add inference metrics**: TTFT, TPOT, throughput at application level
- **Implement distributed tracing**: Track requests across services
- **Enable debug logging**: Configurable verbosity for troubleshooting

### 2. Alerting and SLOs

Define Service Level Objectives for key metrics:

```yaml
# Example SLO for inference latency
- alert: HighTTFT
  expr: histogram_quantile(0.95, ttft_seconds) > 0.5
  annotations:
    summary: "95th percentile TTFT exceeds 500ms"

- alert: LowGPUUtilization
  expr: avg(DCGM_FI_DEV_GPU_UTIL) < 30
  annotations:
    summary: "GPU utilization below 30% - possible inefficiency"
```

### 3. Performance Optimization Workflow

1. **Baseline**: Measure current performance (TTFT, TPOT, GPU utilization)
2. **Identify Bottlenecks**: Use metrics to find constraints (GPU, memory,
   network)
3. **Optimize**: Apply techniques (batching, caching, quantization)
4. **Validate**: Measure improvement and ensure no regression
5. **Monitor**: Continuous tracking to detect degradation

### 4. Cost Optimization

Use observability data to reduce infrastructure costs:

- **Right-size GPU instances**: Match workload to GPU capacity
- **Identify idle resources**: Scale down underutilized GPUs
- **Optimize batch sizes**: Maximize throughput per GPU
- **Cache frequently used prompts**: Reduce redundant computation

### 5. Multi-Tenant Monitoring

For shared AI infrastructure:

- **Per-tenant metrics**: Resource usage, request volume, latency
- **Fair-share enforcement**: Monitor and alert on quota violations
- **Noisy neighbor detection**: Identify workloads impacting others
- **Chargeback/Showback**: Accurate usage attribution for cost allocation

## Integration with Cloud-Native Ecosystem

### Observability Stack

**Recommended Architecture:**

```text
┌─────────────────────────────────────────────────────────────┐
│                     Grafana (Dashboards)                     │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│              Prometheus (Metrics Storage)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ DCGM Exporter│  │ vLLM Metrics │  │ K8s Metrics  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│              OpenTelemetry Collector                         │
│  (Traces, Metrics, Logs from LLM Applications)              │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│          AI Workloads (Inference, Training)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   vLLM       │  │   SGLang     │  │  Training    │      │
│  │   Pods       │  │   Pods       │  │  Jobs        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### CNCF Projects for Observability

- <a href="https://github.com/prometheus/prometheus">`Prometheus`</a>: CNCF
  Graduated. Metrics collection and alerting
- <a href="https://github.com/open-telemetry/opentelemetry-collector">`OpenTelemetry`</a>:
  CNCF Incubating. Unified observability framework
- <a href="https://github.com/grafana/grafana">`Grafana`</a>: CNCF Incubating.
  Visualization and dashboarding
- <a href="https://github.com/grafana/loki">`Loki`</a>: CNCF Incubating. Log
  aggregation
- <a href="https://github.com/jaegertracing/jaeger">`Jaeger`</a>: CNCF
  Graduated. Distributed tracing

## Learning Path

### Phase 1: Foundation (Week 1-2)

- Understand Prometheus metrics and PromQL basics
- Deploy DCGM Exporter and create GPU monitoring dashboards
- Learn OpenTelemetry concepts (traces, metrics, spans)

### Phase 2: Inference Observability (Week 3-4)

- Instrument LLM inference with OpenLLMetry or OpenLit
- Track TTFT, TPOT, and throughput metrics
- Create dashboards for inference performance
- Set up alerts for latency SLOs

### Phase 3: Advanced Topics (Week 5-6)

- Implement distributed tracing across LLM services
- Monitor batch schedulers (Kueue, Volcano)
- Build cost attribution and chargeback dashboards
- Optimize workloads based on observability data

## LLM Capability Evaluation (LLM 能力评测)

Complementing runtime observability, model evaluation measures the quality of
LLM outputs across dimensions such as knowledge, reasoning, code generation,
instruction following, factuality, safety, and multilingual capabilities.

### Open-source Evaluation Frameworks

| Tool | Description |
| --- | --- |
| [lm-eval-harness](https://github.com/EleutherAI/lm-evaluation-harness) | General-purpose evaluation framework with hundreds of task adapters |
| [OpenCompass](https://github.com/open-compass/opencompass) | All-in-one evaluation system with rich task sets, suitable for internal platforms |
| [HELM](https://github.com/stanford-crfm/helm) | Systematic evaluation framework from Stanford with comprehensive dimension design |
| [AlpacaEval](https://github.com/tatsu-lab/alpaca_eval) | Automated pairwise evaluation for instruction following and dialogue quality |
| [lighteval](https://github.com/huggingface/lighteval) | Lightweight evaluation framework from Hugging Face, easy to integrate in CI |
| [EvalPlus](https://github.com/evalplus/evalplus) | Enhanced HumanEval code evaluation with stricter test cases |
| [SWE-bench](https://github.com/princeton-nlp/SWE-bench) | Real software engineering task benchmark for evaluating code agents |
| [FastChat / MT-Bench](https://github.com/lm-sys/FastChat) | Multi-turn dialogue evaluation scripts and benchmarks |
| [Ragas](https://github.com/explodinggradients/ragas) / [DeepEval](https://github.com/confident-ai/deepeval) | RAG pipeline and application-chain quality evaluation |

### Key Benchmark Datasets

- **Knowledge & Language**: MMLU / MMLU-Pro, ARC, HellaSwag, TruthfulQA
- **Reasoning & Math**: GSM8K, MATH, BBH (Big-Bench Hard), AIME
- **Code**: HumanEval / MBPP, EvalPlus, SWE-bench, LiveCodeBench
- **Instruction Following**: MT-Bench, AlpacaEval, IFEval
- **Safety**: AdvBench, HarmBench, RealToxicityPrompts
- **Multilingual**: XNLI, XQuAD / TyDiQA, MIRACL

## References and Further Reading

- [CNCF Observability Landscape](https://landscape.cncf.io/?group=observability-and-analysis)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [OpenTelemetry for LLMs](https://opentelemetry.io/docs/languages/)
- [NVIDIA DCGM Documentation](https://docs.nvidia.com/datacenter/dcgm/)
- [Kubernetes Monitoring Architecture](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)
- See also: [Kubernetes Guide](../kubernetes/README.md) for scheduler metrics
- See also: [Inference Guide](../inference/README.md) for inference platform
  metrics

## RoadMap

Ongoing proposals and discussions:

- Enhanced GPU metrics via DRA (Dynamic Resource Allocation)
- Standardized LLM metrics format across inference engines
- Integration with Kubernetes WG AI Gateway for unified observability
- Cost optimization recommendations based on observability data

---

_This guide consolidates observability best practices for AI infrastructure.
For specific implementation details, refer to the linked documentation for
each layer._
