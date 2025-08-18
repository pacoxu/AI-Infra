# AIBrix: Cloud-Native LLM Inference Infrastructure

[`AIBrix`](https://github.com/vllm-project/aibrix) is an open-source
initiative designed to provide essential building blocks to construct
scalable GenAI inference infrastructure. AIBrix delivers a cloud-native
solution optimized for deploying, managing, and scaling large language
model (LLM) inference, tailored specifically to enterprise needs.

## Overview

AIBrix is part of the vLLM project ecosystem and focuses on providing
enterprise-grade infrastructure for LLM inference at scale. It addresses
the challenges of deploying and managing LLM workloads in production
environments with features like advanced routing, autoscaling, and
distributed inference capabilities.

## Key Features

- **High-Density LoRA Management**: Streamlined support for lightweight,
  low-rank adaptations of models
- **LLM Gateway and Routing**: Efficiently manage and direct traffic
  across multiple models and replicas
- **LLM App-Tailored Autoscaler**: Dynamically scale inference resources
  based on real-time demand
- **Unified AI Runtime**: A versatile sidecar enabling metric
  standardization, model downloading, and management
- **Distributed Inference**: Scalable architecture to handle large
  workloads across multiple nodes
- **Distributed KV Cache**: Enables high-capacity, cross-engine KV reuse
- **Cost-efficient Heterogeneous Serving** (Experimental): Enables mixed
  GPU inference to reduce costs with SLO guarantees
- **GPU Hardware Failure Detection**: Proactive detection of GPU hardware
  issues

## Architecture

AIBrix follows a cloud-native architecture designed for Kubernetes
environments. The system consists of multiple components working together
to provide a comprehensive LLM inference platform:

- **Control Plane**: Manages the lifecycle of inference workloads
- **Gateway**: Handles request routing and load balancing
- **Runtime**: Manages model serving and resource allocation
- **Autoscaler**: Provides intelligent scaling based on LLM-specific
  metrics

## Learning Topics

- LLM-aware load balancing and routing
- Dynamic LoRA switching and management
- Distributed inference architecture
- GPU resource optimization and failure detection
- Cost-efficient heterogeneous serving strategies
- Enterprise-grade LLM deployment patterns

## Project Status

- **Current Version**: v0.4.0 (as of August 2025)
- **License**: Apache 2.0
- **Maturity**: Active development with regular releases
- **Community**: Part of vLLM project with dedicated Slack channel

## Prefill/Decode Disaggregation Support

AIBrix v0.4.0 introduces comprehensive Prefill/Decode (P/D) disaggregation
support with StormService and RoleSet CRDs to enable fine-grained
orchestration of P/D roles, along with routing to unlock disaggregated
inference at scale.

Key features include:

- StormService and RoleSet Custom Resource Definitions (CRDs)
- Fine-grained orchestration of Prefill and Decode roles  
- Advanced routing capabilities for disaggregated inference
- Scalable architecture for large-scale deployments

This feature was delivered through multiple PRs in the v0.4.0 release,
including enhancements to the control plane, gateway routing, and
distributed inference capabilities.

For more details, see [PD Disaggregation](./pd-disaggregation.md).

## Getting Started

### Quick Installation

```bash
# Install component dependencies
AIBRIX_VERSION="v0.4.0"
GITHUB_BASE="https://github.com/vllm-project/aibrix/releases/download"
kubectl apply -f \
  "${GITHUB_BASE}/${AIBRIX_VERSION}/aibrix-dependency-${AIBRIX_VERSION}.yaml" \
  --server-side

# Install AIBrix components  
kubectl apply -f \
  "${GITHUB_BASE}/${AIBRIX_VERSION}/aibrix-core-${AIBRIX_VERSION}.yaml"
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/vllm-project/aibrix.git
cd aibrix

# Install nightly dependencies
kubectl apply -k config/dependency --server-side

# Install nightly components
kubectl apply -k config/default
```

## Resources

- **Documentation**: [aibrix.readthedocs.io](https://aibrix.readthedocs.io/latest/)
- **Blog**: [aibrix.github.io](https://aibrix.github.io/)
- **White Paper**: [arxiv.org/abs/2504.03648](https://arxiv.org/abs/2504.03648)
- **Slack**: [#aibrix](https://vllm-dev.slack.com/archives/C08EQ883CSV)
- **GitHub**: [vllm-project/aibrix](https://github.com/vllm-project/aibrix)

## Notable Presentations

- **KubeCon China 2025**: [AIBrix: Cost-Effective and Scalable Kubernetes
  Control Plane for vLLM](https://kccncchn2025.sched.com/event/1x5im/)
- **KubeCon EU 2025**: [LLM-Aware Load Balancing in Kubernetes: A New Era
  of Efficiency](https://kccnceu2025.sched.com/event/1txC7/) (Keynote
  with Google)
- **ASPLOS'25 Workshop**: [AIBrix: An Open-Source, Large-Scale LLM
  Inference Infrastructure for System
  Research](https://docs.google.com/presentation/d/1YDVsPFTIgGXnROGaJ1VKuDDAB4T5fzpE/edit)
- **FORCE Conference**: [AIBrix 基于vLLM的高性价比LLM推理加速方案—FORCE大会直播回放](https://www.bilibili.com/video/BV1q6MezaEtP/)
  (In Chinese)

---

**Note**: Some content may be generated by AI tools. Please verify
information before using in production environments.
