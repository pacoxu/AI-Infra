---
status: Active
maintainer: pacoxu
last_updated: 2026-01-13
tags: mlops, machine-learning, model-lifecycle, kubernetes
canonical_path: docs/training/mlops.md
---

# MLOps: Machine Learning Operations

## Overview

MLOps (Machine Learning Operations) transforms the model lifecycle into a
repeatable, auditable, and rollback-capable engineering closed-loop. It
combines machine learning development practices with DevOps principles to
streamline the end-to-end ML workflow from data preparation to production
deployment and monitoring.

**Core Objectives:**

- **Repeatability**: Consistent and reproducible ML workflows
- **Auditability**: Full visibility and tracking of model lineage
- **Rollback**: Safe deployment with ability to revert to previous versions
- **Automation**: Reduce manual intervention and human error
- **Collaboration**: Enable seamless teamwork between data scientists and
  engineers

## MLOps Architecture

The MLOps ecosystem can be organized into seven key functional areas:

### 1) 端到端平台 (End-to-End K8s AI Platform)

Complete platforms providing integrated toolchains for the entire ML lifecycle,
designed to be "reference platforms" with strong Kubernetes-native integration.

**Key Platform:**

- <a href="https://github.com/kubeflow/kubeflow">`Kubeflow`</a>: AI platform
  toolkit for Kubernetes, covering composition, modularity and portability,
  from experimentation to production across multiple stages. CNCF project.

**Use Cases:**

- Organizations wanting to standardize on Kubernetes-native workflows
- Teams needing end-to-end visibility and component interoperability

### 2) 流水线与编排 (Pipelines / Orchestration)

Workflow orchestration systems for building, managing, and scheduling complex
ML pipelines with dependencies and parallel execution.

**Key Projects:**

- <a href="https://github.com/kubeflow/pipelines">`Kubeflow Pipelines
  (KFP)`</a>: Container-native workflow orchestration for building and
  deploying portable, scalable ML workflows on Kubernetes. Part of Kubeflow +1
- <a href="https://github.com/argoproj/argo-workflows">`Argo Workflows`</a>:
  Kubernetes-native workflow engine for defining work flows in CRD-based DAG
  or step format. CNCF Graduated +1
- <a href="https://github.com/flyteorg/flyte">`Flyte`</a>: Scalable data/ML/
  analytics workflow orchestration platform with strong type safety and
  reproducibility. CNCF Incubating +1

**Use Cases:**

- Kubernetes-native environments: Argo / KFP
- Complex workflows with strong type requirements and reproducibility: Flyte

### 3) 实验跟踪与模型注册 (Experiment Tracking / Model Registry)

Centralized tracking of experiments, hyperparameters, metrics, and model
artifacts with version control and lineage tracking.

**Key Projects:**

- <a href="https://github.com/mlflow/mlflow">`MLflow`</a>: Open source
  platform covering experiment tracking and model lifecycle management, with
  Model Registry providing centralized version control and metadata
  management. GitHub +1

**Use Cases:**

- Teams needing to track experiments and publish models for engineering
  teams, with standardized registry/lineage views.

### 4) 数据与模型版本管理 (Data/Model Versioning)

Git-like version control systems for managing data and model artifacts,
ensuring reproducibility and enabling rollback.

**Key Projects:**

- <a href="https://github.com/iterative/dvc">`DVC`</a>: Data versioning and
  ML experimentation tool providing Git-like version control for data and
  models, enabling "code version" and "data/model version" to be tracked in
  sync. DVC +1

**Use Cases:**

- Training data versioning for large datasets
- Model artifact versioning across iterations
- Teams requiring strict reproducibility and rollback capabilities

### 5) 数据质量与契约 (Data Quality / Validation)

Frameworks for validating data schemas, quality metrics, and expectations to
prevent data drift and ensure model reliability.

**Key Projects:**

- <a href="https://github.com/great-expectations/great_expectations">`Great
  Expectations`</a>: Data validation and documentation framework for data
  quality unit testing ("expectations" as data quality assertions).
  greatexpectations.io +1

**Use Cases:**

- Teams that have experienced "data drift/garbage data" issues and want to
  integrate data validation into their ML pipelines.

### 6) 特征平台 (Feature Store)

Open-source feature engineering platforms for defining, managing, discovering,
and serving features consistently between training and online inference,
ensuring training-serving consistency.

**Key Projects:**

- <a href="https://github.com/feast-dev/feast">`Feast`</a>: Feature store for
  managing, discovering, and serving ML features, supporting training-serving
  consistency. Feast +1

**Use Cases:**

- Traditional ML (recommendation systems, advertising, risk modeling)
- RAG/LLM scenarios where large-scale structured feature online serving is
  required

### 7) 部署与推理服务 (Serving / Inference)

Model deployment and serving platforms providing inference services with
autoscaling, monitoring, canary deployments, and health checks.

**Key Projects:**

- <a href="https://github.com/kserve/kserve">`KServe`</a>: Kubernetes-native
  model inference platform (CRD) with packaging, auto-scaling, networking,
  health checks, and configuration management for pre-trained model serving.
  KServe Documentation +1
- <a href="https://github.com/SeldonIO/seldon-core">`Seldon Core`</a>:
  Kubernetes-based MLOps/LLMOps framework for packaging, deploying, monitoring
  and managing thousands of production ML models. GitHub +1
- <a href="https://github.com/bentoml/BentoML">`BentoML`</a>: Python-based
  model/AI application serving framework with rapid model packaging,
  containerization, and edge service capabilities. GitHub +1
- <a href="https://github.com/ray-project/ray/tree/master/python/ray/serve">`Ray
  Serve`</a>: Scalable, programmable serving framework (framework-agnostic)
  supporting dynamic batching, multi-model/multi-GPU serving, etc.
  docs.ray.io

**Inference Engine Integration:**

For LLM inference serving, see the [Inference Guide](../inference/README.md)
for deep coverage of:

- <a href="https://github.com/nvidia/TensorRT-LLM">`NVIDIA Triton Inference
  Server`</a>: GPU-optimized multi-framework serving with support for
  multiple backends (TensorRT, ONNX, PyTorch). GitHub +1

**Use Cases:**

- KServe: Kubernetes-native model serving with CRD-based management
- Seldon Core: MLOps framework for large-scale production model deployment
- BentoML: Rapid prototyping and edge deployment
- Ray Serve: Flexible, programmable serving with advanced batching
- Triton: Multi-framework GPU-optimized serving

## Comprehensive MLOps Workflow Projects

End-to-end platforms that span multiple MLOps categories:

- <a href="https://github.com/kubeflow/kubeflow">`Kubeflow`</a>: Machine
  Learning Toolkit for Kubernetes covering pipelines, training, serving, and
  more. See [Kubeflow Training Guide](./kubeflow.md).
- <a href="https://github.com/flyteorg/flyte">`Flyte`</a>: Scalable and
  flexible workflow orchestration platform that seamlessly unifies data, ML
  and analytics stacks. CNCF Incubating.
- <a href="https://github.com/Netflix/metaflow">`Metaflow`</a>: Build, Deploy
  and Manage AI/ML Systems. Originally developed at Netflix.
- <a href="https://github.com/mlflow/mlflow">`MLflow`</a>: Open source
  platform for the machine learning lifecycle covering tracking, projects,
  models, and model registry.
- <a href="https://github.com/polyaxon/polyaxon">`Polyaxon`</a>: MLOps Tools
  For Managing & Orchestrating The Machine Learning LifeCycle.
- <a href="https://github.com/ray-project/ray">`Ray`</a>: Ray is an AI
  compute engine. Ray consists of a core distributed runtime and a set of AI
  Libraries for accelerating ML workloads.
- <a href="https://github.com/zenml-io/zenml">`ZenML`</a>: ZenML: The bridge
  between ML and Ops. Extensible MLOps framework with focus on reproducibility.

## Learning Topics

### Foundation

- **ML Lifecycle Fundamentals:**
  - Model development and experimentation
  - Model training and hyperparameter tuning
  - Model evaluation and validation
  - Model deployment and serving
  - Model monitoring and retraining

- **Version Control:**
  - Code versioning (Git)
  - Data versioning (DVC, Git LFS)
  - Model versioning (MLflow, DVC)
  - Experiment tracking and reproducibility

### Kubernetes Integration

- **Model Serving on Kubernetes:**
  - KServe for standardized model serving
  - Autoscaling based on inference load
  - Canary deployments and A/B testing
  - Resource management for GPU/CPU workloads

- **Training Orchestration:**
  - Distributed training on Kubernetes
  - Gang scheduling for multi-node jobs
  - Integration with training operators (Kubeflow, Volcano)
  - See [Training Guide](./README.md) for comprehensive coverage.

- **Storage and Artifact Management:**
  - Persistent volumes for model storage
  - Object storage integration (S3, GCS, Azure Blob)
  - Caching strategies for datasets
  - See [Fluid](https://github.com/fluid-cloudnative/fluid) for data
    orchestration.

### Automation and CI/CD

- **GitOps for ML:**
  - ArgoCD for declarative deployment
  - Automated retraining pipelines
  - Model versioning and rollback strategies
  - See [ArgoCD Guide](./argocd.md).

- **Pipeline Orchestration:**
  - DAG-based workflows (Argo Workflows, KFP)
  - Dependency management and scheduling
  - Parallel execution and resource optimization
  - Error handling and retry logic

### Monitoring and Observability

- **Model Monitoring:**
  - Prediction accuracy and drift detection
  - Feature distribution monitoring
  - Model performance metrics (latency, throughput)
  - See [Observability Guide](../observability/README.md).

- **Data Quality:**
  - Schema validation and constraints
  - Data quality tests (Great Expectations)
  - Data drift detection
  - Anomaly detection in input features

## Best Practices

### Model Lifecycle Management

- **Version Control Everything:**
  - Track code, data, and model artifacts together
  - Use semantic versioning for models
  - Document model lineage and dependencies
  - Maintain reproducible experiment records

- **Automated Testing:**
  - Unit tests for data preprocessing
  - Integration tests for model pipelines
  - Model performance benchmarks
  - Shadow testing before production deployment

### Deployment Strategies

- **Gradual Rollout:**
  - Canary deployments (1% → 10% → 50% → 100%)
  - A/B testing for model comparison
  - Blue-green deployments for zero-downtime updates
  - Feature flags for controlled rollout

- **Rollback Capabilities:**
  - Maintain previous model versions
  - Quick rollback procedures
  - Automated rollback on performance degradation
  - Document rollback conditions and procedures

### Monitoring and Alerting

- **Key Metrics to Monitor:**
  - Model inference latency (p50, p95, p99)
  - Prediction accuracy and error rates
  - Resource utilization (CPU, GPU, memory)
  - Data drift and feature distribution

- **Alerting Policies:**
  - Set up alerts for model performance degradation
  - Monitor data quality issues
  - Track resource exhaustion
  - Configure on-call rotations for production models

### Collaboration and Documentation

- **Team Collaboration:**
  - Shared experiment tracking (MLflow)
  - Code reviews for model changes
  - Documentation of model decisions
  - Knowledge sharing and post-mortems

- **Model Documentation:**
  - Model cards describing purpose and limitations
  - Training data characteristics and biases
  - Performance metrics and benchmarks
  - Deployment requirements and dependencies

## Case Studies and References

### Industry Implementations

- **Netflix:**
  - [Metaflow: Production ML Infrastructure](https://netflixtechblog.com/open-sourcing-metaflow-a-human-centric-framework-for-data-science-fa72e04a5d9)
  - Focus on data scientist productivity and reproducibility

- **Uber:**
  - [Michelangelo: Uber's ML Platform](https://www.uber.com/blog/michelangelo-machine-learning-platform/)
  - End-to-end ML platform for training, serving, and monitoring

- **Airbnb:**
  - [Bighead: Airbnb's ML Platform](https://databricks.com/session/bighead-airbnbs-end-to-end-machine-learning-platform)
  - Feature engineering and model management at scale

### Research Papers

- **MLOps Principles:**
  - ["Hidden Technical Debt in Machine Learning Systems"](https://papers.nips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html)
    (NIPS 2015)
  - ["Machine Learning: The High-Interest Credit Card of Technical Debt"](https://research.google/pubs/pub43146/)
    (Google Research)

- **Model Serving:**
  - ["Clipper: A Low-Latency Online Prediction Serving System"](https://arxiv.org/abs/1612.03079)
  - ["TensorFlow Serving: Flexible, High-Performance ML Serving"](https://arxiv.org/abs/1712.06139)

## RoadMap (Ongoing Initiatives)

### Kubernetes Enhancements

- **Model as First-Class Citizen:**
  - Native Kubernetes resources for models
  - Built-in model versioning and lineage
  - Integrated model lifecycle management

- **ModelMesh Integration:**
  - Multi-model serving optimization
  - Resource pooling across models
  - Dynamic model loading and unloading

### MLOps Standardization

- **CNCF MLOps Projects:**
  - [Model Spec](https://github.com/modelpack/model-spec): Standardized model
    packaging (CNCF Sandbox)
  - [KServe Evolution](https://github.com/kserve/kserve/issues): Continued
    development of inference standards

- **Industry Standards:**
  - ONNX for model interchange
  - OpenTelemetry for ML observability
  - OpenMetrics for ML metrics

### Emerging Trends

- **LLMOps:**
  - Specialized MLOps practices for large language models
  - Prompt engineering and versioning
  - LLM-specific monitoring and evaluation
  - See [Inference Guide](../inference/README.md) for LLM serving.

- **Federated MLOps:**
  - Cross-cluster model training
  - Privacy-preserving ML workflows
  - Edge deployment and federated learning

## Getting Started

### Prerequisites

- Kubernetes cluster (for deployment)
- Python environment (3.8+)
- Container registry access
- Object storage (S3, GCS, or Azure Blob)

### Quick Start: MLflow Tracking Example

```python
import mlflow

# Start MLflow tracking
mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("my-experiment")

# Log parameters and metrics
with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("batch_size", 32)
    
    # Train model
    model = train_model()
    
    # Log metrics
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("loss", 0.05)
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
```

### Quick Start: Kubeflow Pipeline Example

```python
from kfp import dsl
from kfp import compiler

@dsl.component
def preprocess_data(input_path: str, output_path: str):
    # Data preprocessing logic
    pass

@dsl.component
def train_model(data_path: str, model_path: str):
    # Model training logic
    pass

@dsl.pipeline(name='ml-pipeline')
def ml_pipeline(input_data: str):
    preprocess_task = preprocess_data(
        input_path=input_data,
        output_path='/data/preprocessed'
    )
    
    train_task = train_model(
        data_path=preprocess_task.outputs['output_path'],
        model_path='/models/trained'
    )

# Compile and submit pipeline
compiler.Compiler().compile(ml_pipeline, 'pipeline.yaml')
```

## Contributing

Contributions to MLOps documentation and best practices are welcome! Please
share your experiences, tools, and optimization techniques by opening issues
or pull requests.

## Related Documentation

- [Training on Kubernetes](./README.md): Distributed training and fault
  tolerance
- [Kubeflow Training](./kubeflow.md): Kubeflow Training Operator and Trainer
  V2
- [ArgoCD for GitOps](./argocd.md): GitOps workflows for ML deployments
- [Inference Guide](../inference/README.md): LLM inference and serving
- [Observability](../observability/README.md): Monitoring and metrics for ML
  workloads

---

**Note:** Some content was generated and organized based on community
resources. Please verify technical details with official documentation before
using in production environments.
