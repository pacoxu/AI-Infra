---
status: Active
maintainer: pacoxu
last_updated: 2025-11-04
tags: performance, testing, benchmark, inference, llm
canonical_path: docs/inference/performance-testing.md
---

# Performance Testing & Benchmark Tools for AI/LLM Inference

Performance testing and benchmarking are critical for validating and
optimizing AI/LLM inference systems at scale. This guide covers key tools
and frameworks for testing inference performance, measuring throughput,
latency, and resource utilization in Kubernetes and cloud-native
environments.

## Overview

Performance testing for AI inference involves measuring:

- **Throughput**: Requests per second (RPS) or tokens per second (TPS)
- **Latency**: Time to First Token (TTFT), Time Per Output Token (TPOT),
  Inter-Token Latency (ITL)
- **Resource Utilization**: GPU/CPU usage, memory consumption, network
  bandwidth
- **Scalability**: Performance under varying load and cluster sizes
- **Cost Efficiency**: Performance per dollar, resource optimization

## Kubernetes-Native Performance Testing Tools

### kubernetes-sigs/inference-perf

[`inference-perf`](https://github.com/kubernetes-sigs/inference-perf) is a
Kubernetes-native performance testing framework developed by Kubernetes SIG
Serving. It provides a standardized approach to benchmarking inference
workloads in Kubernetes environments.

**Key Features:**

- Kubernetes-native design with CRDs for test configuration
- Support for multiple inference frameworks (vLLM, TensorRT-LLM, TGI, etc.)
- Standardized metrics collection and reporting
- Integration with Kubernetes scheduling and resource management
- Designed for cloud-native inference platforms

**Use Cases:**

- Benchmarking LLM serving platforms on Kubernetes
- Validating inference performance before production deployment
- Comparing different inference engines and configurations
- Testing autoscaling behavior under load

**Related Resources:**

- [WG Serving Proposal 013](https://github.com/kubernetes-sigs/wg-serving/tree/main/proposals/013-inference-perf):
  Design document for inference-perf

### Azure/kperf

[`kperf`](https://github.com/Azure/kperf) is a Kubernetes
performance benchmarking tool developed by Microsoft Azure. While not
specifically designed for AI workloads, it provides comprehensive cluster
performance testing capabilities.

**Key Features:**

- Cluster-level performance testing
- Pod scheduling and startup latency measurement
- Resource contention testing
- Network and storage performance benchmarking
- Support for large-scale cluster testing

**Use Cases:**

- Validating Kubernetes cluster performance for AI workloads
- Testing pod scheduling latency for inference services
- Measuring cluster resource limits and scalability
- Benchmarking node provisioning and autoscaling

### NVIDIA/knavigator

[`knavigator`](https://github.com/NVIDIA/knavigator) is NVIDIA's
Kubernetes cluster performance testing tool, designed for validating GPU
workload performance and cluster behavior.

**Key Features:**

- GPU-specific performance testing
- Cluster chaos and stress testing
- Job scheduling performance validation
- GPU resource allocation testing
- Large-scale cluster simulation

**Use Cases:**

- Testing GPU cluster performance for AI workloads
- Validating GPU scheduler behavior
- Stress testing AI training and inference clusters
- Measuring GPU resource allocation latency

## Inference Engine-Specific Benchmark Tools

### Triton Inference Server Performance Tools

NVIDIA Triton Inference Server provides comprehensive performance testing
tools:

#### triton-inference-server/perf_analyzer

[`perf_analyzer`](https://github.com/triton-inference-server/perf_analyzer)
is the standard performance testing tool for Triton Inference Server.

**Key Features:**

- Comprehensive inference performance metrics
- Support for multiple model formats (TensorRT, ONNX, PyTorch, etc.)
- Concurrent request testing
- Latency and throughput analysis
- Custom request payload generation

**Use Cases:**

- Benchmarking Triton inference performance
- Optimizing model serving configurations
- Comparing different model formats
- Load testing inference endpoints

#### genai-perf

[`genai-perf`](https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md)
is a specialized tool for benchmarking Large Language Model (LLM) and
generative AI inference.

**Key Features:**

- LLM-specific metrics (TTFT, TPOT, ITL)
- Support for streaming and batch inference
- Token-level performance analysis
- Multiple LLM framework support (vLLM, TGI, TensorRT-LLM)
- Realistic workload generation

**Use Cases:**

- Benchmarking LLM serving performance
- Measuring token generation latency
- Testing streaming inference endpoints
- Comparing LLM inference engines

### vLLM Benchmark Tools

#### vllm-project/vllm benchmark_serving.py

[`benchmark_serving.py`](https://github.com/vllm-project/vllm/blob/main/benchmarks/benchmark_serving.py)
is vLLM's built-in benchmarking script for testing serving performance.

**Key Features:**

- Native vLLM integration
- Support for OpenAI-compatible API testing
- Configurable request patterns and load profiles
- Token generation metrics
- Throughput and latency analysis

**Use Cases:**

- Benchmarking vLLM serving deployments
- Testing different vLLM configurations
- Measuring performance under various load patterns
- Comparing vLLM with other inference engines

### fmperf-project/fmperf

[`fmperf`](https://github.com/fmperf-project/fmperf) is a
comprehensive benchmarking framework for Foundation Models (FM) and Large
Language Models.

**Key Features:**

- Multi-framework support (vLLM, TGI, TensorRT-LLM, etc.)
- Standardized benchmark suite
- Realistic workload patterns
- Comprehensive metrics collection
- Performance comparison reports

**Use Cases:**

- Comparing different LLM inference engines
- Standardized foundation model benchmarking
- Production workload simulation
- Performance regression testing

## Cloud Platform-Specific Tools

### GCP latency-profile-generator

[`latency-profile-generator`](https://github.com/GoogleCloudPlatform/ai-on-gke/tree/main/benchmarks/benchmark/tools/profile-generator)
is Google Cloud's tool for generating realistic latency profiles for AI
inference workloads.

**Key Features:**

- Realistic request pattern generation
- GCP-specific optimizations
- Integration with GKE and Vertex AI
- Workload profiling for autoscaling
- Custom latency distribution modeling

**Use Cases:**

- Generating test workloads for GCP AI services
- Profiling production traffic patterns
- Testing autoscaling configurations
- Capacity planning for GKE AI workloads

## Load Testing and Stress Testing Tools

### openshift-psap/llm-load-test

[`llm-load-test`](https://github.com/openshift-psap/llm-load-test) is a load
testing framework specifically designed for LLM inference services,
developed by Red Hat's OpenShift PSAP team.

**Key Features:**

- Kubernetes-native load testing
- LLM-specific workload patterns
- OpenShift and Kubernetes support
- Metrics collection and visualization
- Integration with AI inference platforms

**Use Cases:**

- Load testing LLM serving on OpenShift/Kubernetes
- Validating production readiness
- Stress testing inference endpoints
- Capacity planning and resource sizing

## Industry Standards and Benchmarks

### MLCommons Inference

[`MLCommons Inference`](https://docs.mlcommons.org/inference/)
provides standardized benchmarks for AI inference across different hardware
and software platforms.

**Key Features:**

- Industry-standard benchmark suite
- Multiple model categories (CV, NLP, Recommender Systems)
- Hardware and software agnostic
- Reproducible results with strict guidelines
- Official performance leaderboards

**Use Cases:**

- Comparing hardware platforms for AI inference
- Validating inference performance against industry standards
- Hardware procurement decisions
- Performance marketing and validation

### sgl-project/genai-bench

[`genai-bench`](https://github.com/sgl-project/genai-bench) is a
comprehensive benchmark suite for generative AI workloads, developed by the
SGLang project.

**Key Features:**

- Focus on generative AI workloads
- Multiple model types (LLM, vision, multimodal)
- Realistic task evaluation
- Integration with popular inference frameworks
- Performance and quality metrics

**Use Cases:**

- Benchmarking generative AI applications
- Comparing inference engines for multimodal models
- Evaluating end-to-end application performance
- Quality vs. performance trade-off analysis

## Best Practices for Performance Testing

### Test Environment Setup

- **Consistent Hardware**: Use dedicated GPU nodes or consistent instance
  types
- **Network Isolation**: Minimize network interference during tests
- **Warm-up Period**: Allow models to warm up before collecting metrics
- **Multiple Runs**: Perform multiple test runs for statistical significance

### Metrics Collection

- **Latency Percentiles**: Track P50, P90, P95, P99 latencies
- **Throughput Under Load**: Measure RPS/TPS at different load levels
- **Resource Utilization**: Monitor GPU, CPU, memory, and network usage
- **Error Rates**: Track request failures and timeout rates

### Workload Design

- **Realistic Patterns**: Use production-like request patterns
- **Variable Input Length**: Test with different input token lengths
- **Batch vs. Streaming**: Test both batch and streaming inference modes
- **Concurrent Requests**: Measure performance under concurrent load

### Comparison and Validation

- **Baseline Metrics**: Establish baseline performance for comparison
- **Configuration Testing**: Test different model configurations (batch
  size, precision, etc.)
- **Framework Comparison**: Compare different inference engines with same
  models
- **Cost Analysis**: Calculate performance per dollar metrics

## Learning Topics

- Understanding inference performance metrics (TTFT, TPOT, ITL)
- Kubernetes-native performance testing strategies
- GPU performance profiling and optimization
- Autoscaling based on inference metrics
- Comparing inference engines and deployment strategies
- Production load testing and capacity planning

## KubeCon References

- [KubeCon EU 2025: Performance Testing for AI/ML Workloads](https://kccnceu2025.sched.com/event/1tx7Q)

## Additional Resources

- [Chinese article on LLM performance testing](https://mp.weixin.qq.com/s/6vfE_VGF66vDmh2R4RTC1g)
- Kubernetes SIG Serving documentation on inference performance
- NVIDIA optimization guides for inference workloads
- Cloud provider best practices for AI inference

## Related Documentation

- [Inference Guide](./README.md): Overview of inference engines and
  platforms
- [Model Lifecycle](./model-lifecycle.md): Cold-start optimization and model
  management
- [Caching](./caching.md): KV cache optimization for performance
- [AIBrix](./aibrix.md): Cloud-native LLM inference with built-in
  performance optimization

---

**Note:** Some content in this guide was generated with AI assistance. Please
verify tool versions, features, and links before use in production
environments.
