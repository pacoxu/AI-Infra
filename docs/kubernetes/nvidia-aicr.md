---
status: Active
maintainer: pacoxu
last_updated: 2026-03-13
tags: kubernetes, nvidia, gpu, cluster-setup, recipes, helm, argocd
canonical_path: docs/kubernetes/nvidia-aicr.md
---

# NVIDIA AI Cluster Runtime (AICR)

<a href="https://github.com/NVIDIA/aicr">**NVIDIA AI Cluster Runtime
(AICR)**</a> is a CLI tooling project that makes it easy to stand up
GPU-accelerated Kubernetes clusters. It captures known-good combinations
of drivers, operators, kernels, and system configurations and publishes them
as version-locked **recipes** — reproducible artifacts for Helm, ArgoCD, and
other deployment frameworks.

## Overview

Running GPU-accelerated Kubernetes clusters reliably is hard. Small differences
in kernel versions, drivers, container runtimes, operators, and Kubernetes
releases can cause failures that are difficult to diagnose and expensive to
reproduce. AICR makes validated configurations available to everyone by
encoding them as composable, layered overlays.

### Key Properties of Every Recipe

- **Optimized** — Tuned for a specific combination of hardware, cloud, OS, and
  workload intent
- **Validated** — Passes automated constraint and compatibility checks before
  publishing
- **Reproducible** — Same inputs produce identical deployments every time

## Core Components

### 1. `aicr` CLI

Single binary that serves as the primary interface. Key subcommands:

| Command | Description |
| ------- | ----------- |
| `aicr snapshot` | Captures the current cluster state (GPU hardware, drivers, OS, operators) into a YAML snapshot |
| `aicr recipe` | Generates a validated, version-locked recipe for a target environment |
| `aicr bundle` | Materializes a recipe into deployment-ready Helm charts |
| `aicr validate` | Validates a recipe against a live cluster snapshot |

### 2. API Server (`aicrd`)

REST API server exposing the same capabilities as the CLI. Designed for
in-cluster use in CI/CD pipelines or air-gapped environments.

### 3. Snapshot Agent

A Kubernetes Job that captures live cluster state (GPU hardware, drivers, OS,
operators) into a ConfigMap for validation against recipes.

## Quick Start

```bash
# Install the CLI (Homebrew)
brew tap NVIDIA/aicr
brew install aicr

# Or use the install script
curl -sfL https://raw.githubusercontent.com/NVIDIA/aicr/main/install | bash -s --

# Capture your cluster's current state
aicr snapshot --output snapshot.yaml

# Generate a validated recipe for your environment
aicr recipe --service eks --accelerator h100 --os ubuntu \
  --intent training --platform kubeflow -o recipe.yaml

# Validate the recipe against your cluster
aicr validate --recipe recipe.yaml --snapshot snapshot.yaml

# Render into deployment-ready Helm charts
aicr bundle --recipe recipe.yaml --output ./bundles

# Validate your cluster (deployment, performance, conformance)
aicr validate --recipe recipe.yaml --phase all --output report.json
```

The `bundles/` directory contains per-component Helm charts with values files,
checksums, and deployer configs. Deploy with `helm install`, commit to a GitOps
repo, or use the built-in ArgoCD deployer.

## Supported Environments

| Dimension | This Release |
| --------- | ------------ |
| **Kubernetes** | Amazon EKS, Google GKE, self-managed (Kind) |
| **GPUs** | NVIDIA H100, GB200 |
| **OS** | Ubuntu |
| **Workloads** | Training (Kubeflow), Inference (Dynamo) |
| **Components** | GPU Operator, Network Operator, cert-manager, Prometheus stack |

## How It Works

A **recipe** is a version-locked configuration for a specific environment.
You describe your target (cloud, GPU, OS, workload intent), and the recipe
engine matches it against a library of validated **overlays** — layered
configurations that compose bottom-up from base defaults through cloud,
accelerator, OS, and workload-specific tuning.

The **bundler** materializes a recipe into deployment-ready artifacts: one
folder per component, each with Helm values, checksums, and a README. The
**validator** compares a recipe against a live cluster snapshot and flags
anything out of spec.

This separation means the same validated configuration works whether you deploy
with Helm, ArgoCD, Flux, or a custom pipeline.

## Supply Chain Security

Every AICR release includes:

- SLSA Level 3 provenance
- Signed SBOMs
- Image attestations (cosign)
- Checksum verification on every component

## Relation to Other NVIDIA Tools

| Tool | Purpose |
| ---- | ------- |
| [GPU Operator](./nvidia-gpu-operator.md) | Manages the lifecycle of GPU drivers, device plugins, and monitoring on Kubernetes nodes |
| **AICR** | Higher-level cluster recipe tool that orchestrates GPU Operator and other components into a validated, version-locked deployment |
| [DRA Driver](./dra.md) | Provides flexible GPU resource allocation via Dynamic Resource Allocation |

AICR sits **above** the GPU Operator: it generates the Helm values and
deployment configuration that installs and configures the GPU Operator (along
with Network Operator, cert-manager, Prometheus, etc.) in a known-good
combination.

## Learning Topics

- Cluster bootstrapping and configuration management for GPU workloads
- Supply chain security for Kubernetes cluster components
- GitOps patterns for cluster lifecycle management
- Recipe-based infrastructure as code
- Difference between per-node GPU management (GPU Operator) and cluster-level
  configuration management (AICR)

## References

- <a href="https://github.com/NVIDIA/aicr">GitHub: NVIDIA/aicr</a>
- [NVIDIA GPU Operator](./nvidia-gpu-operator.md)
- [Dynamic Resource Allocation (DRA)](./dra.md)
