---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: training, argocd, gitops, continuous-deployment
canonical_path: docs/training/argocd.md
---

# ArgoCD for AI Workload Management

## Overview

<a href="https://github.com/argoproj/argo-cd">`ArgoCD`</a> is a
CNCF Graduated project that provides declarative, GitOps continuous delivery
for Kubernetes. In the context of AI infrastructure, ArgoCD enables teams to
manage, version, and deploy ML training jobs, inference services, and data
pipelines using Git as the single source of truth.

## Why ArgoCD for AI Workloads?

### Key Benefits

1. **GitOps Workflow**
   - Version control for ML job configurations
   - Audit trail for all changes
   - Easy rollback to previous versions
   - Collaborative review process via pull requests

2. **Declarative Configuration**
   - Define training jobs, models, and infrastructure as code
   - Reproducible deployments across environments
   - Consistent configuration management

3. **Multi-Environment Support**
   - Manage dev, staging, and production environments
   - Progressive rollout of new models
   - Environment-specific configurations

4. **Automation and Self-Healing**
   - Automatic synchronization with Git repository
   - Self-healing for drift detection
   - Automated deployment pipelines

## ArgoCD in the Kubeflow Ecosystem

ArgoCD complements Kubeflow by providing continuous deployment capabilities
for ML workloads. As shown in the
<a href="https://mp.weixin.qq.com/s/qFmMduuQtgOdjwQLaT95dw">Kubeflow
ecosystem architecture</a> (Chinese language resource) and referenced in the
<a href="https://argo-cd.readthedocs.io/">official ArgoCD documentation</a>,
ArgoCD integrates with various Kubeflow components:

![Kubeflow Ecosystem](https://github.com/user-attachments/assets/bc87980f-37d8-452f-ae1d-94cadc53a8f1)

### Integration Points

**Kubeflow Components:**

- Jupyter Notebook deployments
- Training Operators (PyTorch, TensorFlow, XGBoost)
- Kubeflow Pipelines
- Tensorboard for visualization
- Katib hyperparameter tuning jobs
- KServe model serving deployments
- MPI Operator for distributed training
- Kubeflow Metadata tracking
- Recurring Jobs scheduling

**Infrastructure Components:**

- Istio service mesh configuration
- Knative serverless functions
- cert-manager certificates
- MinIO object storage
- Dex identity management

## ArgoCD Architecture for ML Workflows

### Components

1. **Git Repository**: Source of truth for all configurations
   - Training job definitions
   - Model serving configurations
   - Pipeline definitions
   - Infrastructure manifests

2. **ArgoCD Application**: Defines deployment strategy
   - Source repository and branch
   - Target Kubernetes namespace
   - Sync policy (manual or automatic)
   - Health checks and status

3. **Kubernetes Cluster**: Target deployment environment
   - Training jobs (PyTorchJob, TFJob)
   - Inference services (KServe)
   - ML pipelines (Kubeflow Pipelines)

## GitOps Workflow for Training Jobs

### Repository Structure

```text
ml-training-repo/
├── base/
│   ├── kustomization.yaml
│   └── pytorch-job-template.yaml
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── patches.yaml
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── patches.yaml
│   └── prod/
│       ├── kustomization.yaml
│       └── patches.yaml
└── argocd/
    ├── training-dev.yaml
    ├── training-staging.yaml
    └── training-prod.yaml
```

### Example: PyTorch Training Job in Git

```yaml
# base/pytorch-job-template.yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: pytorch-distributed-training
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
            command:
              - python
              - train.py
            resources:
              limits:
                nvidia.com/gpu: 1
    Worker:
      replicas: 3
      restartPolicy: OnFailure
      template:
        spec:
          containers:
          - name: pytorch
            image: pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
            command:
              - python
              - train.py
            resources:
              limits:
                nvidia.com/gpu: 1
```

### ArgoCD Application Definition

```yaml
# argocd/training-prod.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ml-training-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/ml-training-repo
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: ml-training
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

## Managing Training Jobs with ArgoCD

### Deployment Workflow

1. **Define Training Job**: Create PyTorchJob or TFJob manifest in Git
2. **Commit to Repository**: Push changes to feature branch
3. **Code Review**: Team reviews job configuration via pull request
4. **Merge to Main**: Approved changes merged to main branch
5. **ArgoCD Sync**: ArgoCD detects changes and syncs to cluster
6. **Job Execution**: Kubernetes creates pods and runs training
7. **Monitoring**: Track job status in ArgoCD UI and Kubeflow dashboard

### Progressive Rollout Strategy

```yaml
# Progressive rollout with ArgoCD sync waves
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: llm-training-v2
  annotations:
    argocd.argoproj.io/sync-wave: "1"  # Deploy after infrastructure
spec:
  # Job configuration
```

### Handling Job Updates

#### Scenario: Update training hyperparameters

```bash
# 1. Clone repository
git clone https://github.com/your-org/ml-training-repo
cd ml-training-repo

# 2. Create feature branch
git checkout -b update-learning-rate

# 3. Update job configuration
vim overlays/prod/patches.yaml
# Change learning rate from 0.001 to 0.0005

# 4. Commit and push
git add overlays/prod/patches.yaml
git commit -m "Update learning rate to 0.0005"
git push origin update-learning-rate

# 5. Create pull request and merge after review

# 6. ArgoCD automatically syncs the change
```

## Integration with CI/CD Pipelines

### GitHub Actions + ArgoCD

```yaml
# .github/workflows/deploy-training.yaml
name: Deploy Training Job
on:
  push:
    branches: [main]
    paths:
      - 'overlays/prod/**'

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate Kubernetes manifests
        run: |
          kubectl --dry-run=client apply -f overlays/prod/
      
      - name: Trigger ArgoCD Sync
        env:
          ARGOCD_SERVER: ${{ secrets.ARGOCD_SERVER }}
          ARGOCD_TOKEN: ${{ secrets.ARGOCD_TOKEN }}
        run: |
          argocd app sync ml-training-prod --grpc-web
```

### Pre-Sync Hooks for Data Preparation

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: prepare-training-data
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      containers:
      - name: data-prep
        image: python:3.11
        command:
          - python
          - prepare_data.py
      restartPolicy: Never
```

## Multi-Cluster Training Management

### Scenario: Training Across Multiple Regions

ArgoCD supports deploying training jobs to multiple Kubernetes clusters:

```yaml
# argocd/training-us-west.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ml-training-us-west
spec:
  destination:
    server: https://us-west-k8s.example.com
    namespace: ml-training
  source:
    repoURL: https://github.com/your-org/ml-training-repo
    path: overlays/us-west

---
# argocd/training-eu-central.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ml-training-eu-central
spec:
  destination:
    server: https://eu-central-k8s.example.com
    namespace: ml-training
  source:
    repoURL: https://github.com/your-org/ml-training-repo
    path: overlays/eu-central
```

## Monitoring and Observability

### ArgoCD Application Health

ArgoCD provides health status for training jobs:

- **Healthy**: All pods running successfully
- **Progressing**: Job is being deployed or running
- **Degraded**: Some pods failed or job encountered errors
- **Suspended**: Job is paused or waiting for resources
- **Missing**: Job definition not found in cluster

### Custom Health Checks

```yaml
# Custom health check for PyTorchJob
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: pytorch-training
spec:
  # ... other configuration
  ignoreDifferences:
  - group: kubeflow.org
    kind: PyTorchJob
    jsonPointers:
    - /status
  # Custom health assessment
  health:
    status: Progressing
    message: "Training job is running"
```

### Integration with Prometheus

Monitor ArgoCD metrics for ML workload deployments:

```promql
# Number of out-of-sync ML training applications
argocd_app_info{namespace="ml-training",sync_status="OutOfSync"}

# Deployment frequency
rate(argocd_app_sync_total{namespace="ml-training"}[1h])

# Failed synchronizations
argocd_app_sync_total{namespace="ml-training",phase="Failed"}
```

## Best Practices for AI Workloads

### 1. Separate Configuration from Code

- Store training scripts in separate repositories
- Use container images for code
- Manage job configurations in ArgoCD-tracked repositories

### 2. Environment-Specific Configurations

```text
overlays/
├── dev/          # Small dataset, single GPU, frequent updates
├── staging/      # Medium dataset, 4 GPUs, pre-production validation
└── prod/         # Full dataset, 16+ GPUs, stable releases
```

### 3. Version Control Strategies

- Use semantic versioning for training job definitions
- Tag releases for production deployments
- Maintain separate branches for experiments

### 4. Secrets Management

```yaml
# Use sealed secrets or external secret operators
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: training-secrets
spec:
  encryptedData:
    api-key: AgBhQ3J...  # Encrypted API key
```

### 5. Resource Quotas and Limits

Define resource constraints to prevent runaway jobs:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ml-training-quota
spec:
  hard:
    requests.nvidia.com/gpu: "32"
    requests.cpu: "256"
    requests.memory: "1024Gi"
```

## Troubleshooting

### Common Issues

#### 1. Application Out of Sync

```bash
# Check differences
argocd app diff ml-training-prod

# Force sync
argocd app sync ml-training-prod --force
```

#### 2. Training Job Stuck in Pending

```bash
# Check ArgoCD logs
argocd app logs ml-training-prod

# Check Kubernetes events
kubectl describe pytorchjob pytorch-training -n ml-training
```

#### 3. Sync Hooks Failing

```bash
# View hook logs
argocd app logs ml-training-prod --kind Job
```

## Comparison with Other CD Tools

### ArgoCD vs Flux CD

- **ArgoCD**: Web UI, multi-tenancy, ApplicationSet for multiple clusters
- **Flux CD**: Lighter weight, native Kubernetes, HelmRelease CRD

### ArgoCD vs Jenkins

- **ArgoCD**: GitOps, declarative, Kubernetes-native
- **Jenkins**: Imperative, general-purpose CI/CD, requires plugins for K8s

### ArgoCD vs Kubeflow Pipelines

- **ArgoCD**: Deployment and lifecycle management
- **Kubeflow Pipelines**: ML workflow orchestration and experimentation
- **Together**: ArgoCD deploys Pipelines, Pipelines orchestrate training

## Learning Resources

### Official Documentation

- <a href="https://argo-cd.readthedocs.io/">ArgoCD Documentation</a>
- <a href="https://github.com/argoproj/argo-cd">ArgoCD GitHub Repository</a>
- <a href="https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/">ArgoCD
  Best Practices</a>

### Community Resources

- <a href="https://mp.weixin.qq.com/s/qFmMduuQtgOdjwQLaT95dw">Kubeflow
  Ecosystem with ArgoCD</a> (Chinese)
- <a href="https://www.cncf.io/blog/2023/01/12/argo-cd-best-practices/">CNCF
  ArgoCD Blog</a>
- <a href="https://argoproj.github.io/community/">ArgoCD Community</a>

### Tutorials

- <a href="https://argo-cd.readthedocs.io/en/stable/getting_started/">Getting
  Started with ArgoCD</a>
- <a href="https://codefresh.io/learn/argo-cd/">ArgoCD Tutorial by
  Codefresh</a>

## Related Projects in Argo Ecosystem

- <a href="https://github.com/argoproj/argo-workflows">`Argo Workflows`</a>:
  Kubernetes-native workflow engine (CNCF Graduated)
- <a href="https://github.com/argoproj/argo-rollouts">`Argo Rollouts`</a>:
  Progressive delivery for Kubernetes
- <a href="https://github.com/argoproj/argo-events">`Argo Events`</a>:
  Event-driven workflow automation

## Roadmap and Future Development

### Upcoming Features

- Enhanced ApplicationSet for dynamic app generation
- Improved support for Helm charts and Kustomize
- Better integration with cloud-native security tools
- Advanced deployment strategies (blue-green, canary)

## Contributing

Contributions to ArgoCD are welcome! See the
<a href="https://github.com/argoproj/argo-cd/blob/master/CONTRIBUTING.md">contributing
guide</a> for more information.

---

**Note:** Some content may be generated or summarized from referenced sources.
Please verify technical details with official documentation before using in
production environments.
