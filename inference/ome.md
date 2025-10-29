# OME: Kubernetes Operator for LLM Management

OME is a comprehensive Kubernetes operator designed for enterprise-grade
management and serving of Large Language Models (LLMs). Developed by the
SGL project team, OME optimizes the deployment and operation of LLMs through
automated model management, intelligent runtime selection, and sophisticated
deployment patterns.

## Overview

[`OME`](https://github.com/sgl-project/ome) stands out in the LLM inference
landscape by treating models as first-class Kubernetes custom resources,
enabling sophisticated model parsing, automated runtime selection, and
advanced deployment patterns including prefill-decode disaggregation.

**Note**: [contributors](https://github.com/sgl-project/ome/graphs/contributors) shows this is a one-person project(104/168 commits) until now.

## Key Features

### Model Management

- **First-class Custom Resources**: Models are managed as native Kubernetes
  resources with comprehensive metadata extraction
- **Architecture Detection**: Automatic parsing of model files to extract
  architecture, parameter count, and capabilities
- **Multi-format Support**: Supports SafeTensors, PyTorch, TensorRT, and ONNX
  model formats
- **Distributed Storage**: Automated repair, double encryption, and namespace
  scoping for secure model storage

### Intelligent Runtime Selection

- **Automatic Matching**: Weighted scoring system matches models to optimal
  runtime configurations
- **Multi-factor Analysis**: Considers architecture, format, quantization,
  parameter size, and framework compatibility
- **Performance Optimization**: Ensures each model runs on the most suitable
  inference engine

### Advanced Deployment Patterns

- **Prefill-Decode Disaggregation**: Supports sophisticated PD disaggregation
  for improved resource utilization
- **Multi-node Inference**: Distributes large models across multiple nodes
- **Traditional Deployments**: Standard Kubernetes deployments with advanced
  scaling controls

### Resource Optimization

- **GPU Bin-packing**: Specialized scheduling algorithm for optimal GPU
  utilization
- **Dynamic Re-optimization**: Continuous cluster efficiency optimization
  while maintaining high availability
- **Smart Resource Allocation**: Maximizes hardware utilization across
  heterogeneous environments

## Runtime Integrations

### SGLang (First-class Support)

OME provides deep integration with
[`SGLang`](https://github.com/sgl-project/sglang), featuring:

- Cache-aware load balancing
- Multi-node deployment capabilities
- Prefill-decode disaggregated serving
- Multi-LoRA adapter serving
- Advanced inference optimizations

### vLLM Support

OME supports [`vLLM`](https://github.com/vllm-project/vllm) as a high-performance
runtime option with [built-in configurations](https://github.com/sgl-project/ome/tree/main/config/runtimes/vllm)
for optimized LLM serving.

## Kubernetes Ecosystem Integration

OME integrates deeply with modern Kubernetes components:

- **[Kueue](https://kueue.sigs.k8s.io/)**: Gang scheduling for multi-pod
  workloads
- **[LeaderWorkerSet](https://github.com/kubernetes-sigs/lws)**: Resilient
  multi-node deployments
- **[KEDA](https://keda.sh/)**: Advanced custom metrics-based autoscaling
- **[K8s Gateway API](https://gateway-api.sigs.k8s.io/)**: Sophisticated
  traffic routing
- **[Gateway API Inference Extension](https://gateway-api-inference-extension.sigs.k8s.io/)**:
  Standardized inference endpoints

## Core Architecture

OME uses a component-based architecture built on Kubernetes custom resources:

### Custom Resources

- **BaseModel/ClusterBaseModel**: Define model sources and metadata
- **ServingRuntime/ClusterServingRuntime**: Define how models are served
- **InferenceService**: Connects models to runtimes for deployment
- **BenchmarkJob**: Measures model performance under different workloads

### Automated Workflow

1. **Model Discovery**: Downloads and parses models to understand
   characteristics
2. **Runtime Selection**: Selects optimal runtime configuration for each model
3. **Resource Generation**: Generates Kubernetes resources for efficient
   deployment
4. **Continuous Optimization**: Optimizes resource utilization across the
   cluster

## Production Readiness

OME is production-ready with:

- ✅ API version: v1beta1
- ✅ Comprehensive documentation
- ✅ Unit and integration test coverage
- ✅ Large-scale production deployments
- ✅ Standard Kubernetes monitoring and events
- ✅ RBAC-based security and model encryption
- ✅ High availability with redundant storage

## Installation

### Requirements

Requires Kubernetes 1.28 or newer

### Quick Start (OCI Registry)

```bash
# Install OME CRDs
helm upgrade --install ome-crd oci://ghcr.io/moirai-internal/charts/ome-crd \
  --namespace ome --create-namespace

# Install OME resources
helm upgrade --install ome oci://ghcr.io/moirai-internal/charts/ome-resources \
  --namespace ome
```

### Helm Repository

```bash
# Add repository
helm repo add ome https://sgl-project.github.io/ome
helm repo update

# Install components
helm upgrade --install ome-crd ome/ome-crd \
  --namespace ome --create-namespace
helm upgrade --install ome ome/ome-resources --namespace ome
```

## Learning Topics

- Kubernetes custom resource development and patterns
- LLM inference optimization strategies
- Multi-node distributed serving architectures
- Resource scheduling and bin-packing algorithms
- Model management and metadata extraction
- Production MLOps patterns in Kubernetes

## Comparison with Other Platforms

OME distinguishes itself through:

- **Native Kubernetes Integration**: Deep CRD-based architecture vs external
  orchestration
- **Intelligent Runtime Selection**: Automated matching vs manual configuration
- **Advanced Deployment Patterns**: Built-in PD disaggregation and multi-node
  support
- **Model-First Design**: Models as first-class resources vs
  deployment-focused approaches

## Roadmap

- Enhanced model parsing for additional model families and architectures
- Support for model quantization and optimization workflows
- Federation across multiple Kubernetes clusters
- Extended runtime ecosystem integrations

## References

- [OME GitHub Repository](https://github.com/sgl-project/ome)
- [OME Documentation](https://sgl-project.github.io/ome/docs/)
- [SGLang Project](https://github.com/sgl-project/sglang)
- [Installation Guide](https://sgl-project.github.io/ome/docs/installation/)
- [API Reference](https://sgl-project.github.io/ome/docs/reference/ome.v1beta1/)

---

**Note**: This documentation provides an overview of OME capabilities. For
detailed implementation guidance and advanced configurations, refer to the
official OME documentation.
