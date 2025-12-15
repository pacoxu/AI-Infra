---
status: Active
maintainer: pacoxu
date: 2025-12-15
tags: ai-infrastructure, ray, vllm, pytorch, kubernetes, data-processing
canonical_path: docs/blog/2025-12-15/sql-to-inference.md
---

# From SQL on CPUs to Inference on GPUs: The Evolution of AI Data Processing

**Based on PyTorchCon 2025 Presentation: "An Open Source Post-Training Stack:
Kubernetes + Ray + PyTorch + vLLM" by Robert Nishihara, Co-founder of Anyscale**

## Introduction

The AI infrastructure landscape is undergoing a fundamental transformation.
Just as the LAMP stack (Linux, Apache, MySQL, PHP) defined the internet era,
a new technology stack is emerging to power the AI era. At the recent
PyTorchCon 2025, Robert Nishihara from Anyscale introduced the concept of the
**PARK stack** (PyTorch + AI + Ray + Kubernetes), which is rapidly becoming
the default platform for large-scale AI deployments.

This blog explores two critical aspects of this transformation:

1. **New Workloads**: How AI data processing is shifting from SQL on CPUs to
   inference on GPUs
2. **The Co-evolving Stack**: How vLLM + Ray and Ray + Kubernetes are
   evolving together

## Part 1: New Workloads — From SQL on CPUs to Inference on GPUs

### The Paradigm Shift in Data Processing

Traditional data processing centered around structured tabular data processed
with SQL queries on CPU clusters. The AI era introduces a fundamentally
different workload:

| Dimension | Traditional (SQL) | AI Data Processing |
| --------- | ----------------- | ------------------ |
| **Data Type** | Tabular Data | Multimodal Data (images, video, audio, text, sensor) |
| **Processing** | Regular processing | Inference + regular processing |
| **Compute** | CPUs | CPUs & GPUs |

**Key Insight**: The shift in the nature of data processing is not just about
adding GPUs - it's about fundamentally changing what data means and how we
process it.

### Why This Shift Matters

The transformation from SQL on CPUs to inference on GPUs represents more than
a hardware change:

1. **Data Complexity**: Moving from structured tables to rich multimodal data
   that captures the real world in images, videos, audio, and sensor readings

2. **Processing Paradigm**: Traditional SQL queries are being supplemented
   (and sometimes replaced) by inference operations that extract meaning from
   unstructured data

3. **Resource Requirements**: GPU acceleration becomes essential not just for
   training, but for production data processing pipelines

4. **Scale Challenges**: Managing distributed GPU workloads requires new
   orchestration patterns beyond traditional database clusters

### Real-World Impact

This shift enables new applications that were previously impossible:

- **Autonomous Systems**: Processing sensor data, camera feeds, and LiDAR in
  real-time
- **Content Understanding**: Analyzing images and videos at scale for
  recommendations and moderation
- **Voice Interfaces**: Real-time speech recognition and natural language
  understanding
- **Document Intelligence**: Extracting structured information from
  unstructured documents

The infrastructure must evolve to support these workloads efficiently.

## Part 2: The Co-evolving Stack — vLLM + Ray & Ray + Kubernetes

### Understanding the PARK Stack

At Linux Foundation's Open Source Summit Japan, Jim Zemlin introduced the
**PARK technology stack**:

- **P**: PyTorch (the dominant AI framework)
- **A**: AI (models and algorithms)
- **R**: Ray (distributed computing framework for large-scale AI/ML)
- **K**: Kubernetes (cloud-native orchestration)

Just as LAMP defined web infrastructure, PARK is defining the AI infrastructure
generation.

### The Co-evolution of vLLM and Ray

**Why Ray is Everywhere**: Nearly every open-source Reinforcement Learning
(RL) framework is built on Ray as the orchestrator:

| Framework | Training Engine | Serving Engine | Orchestrator |
| --------- | --------------- | -------------- | ------------ |
| TRL (Hugging Face) | Hugging Face Trainer | Hugging Face, vLLM | **Ray** |
| Verl (ByteDance) | FSDP, DeepSpeed, Megatron | vLLM, SGLang | **Ray** |
| OpenRLHF | DeepSpeed | Hugging Face, vLLM | **Ray** |
| AReaL (Ant Group) | DeepSpeed, Megatron | vLLM, SGLang | **Ray** |
| Prime RL | FSDP | vLLM | **Ray** |
| ROLL (Alibaba) | DeepSpeed, Megatron | vLLM, SGLang | **Ray** |
| NeMo-RL (Nvidia) | FSDP, Megatron | vLLM | **Ray** |
| SkyRL (UC Berkeley) | FSDP, DeepSpeed | vLLM, SGLang, OpenAI | **Ray** |
| SLIME (Z.ai) | Megatron | SGLang | **Ray** |
| RAGEN | Verl backend | Hugging Face, vLLM, SGLang | **Ray** |

**Key Pattern**: Ray provides the orchestration layer that connects training
engines (FSDP, DeepSpeed, Megatron) with serving engines (vLLM, SGLang),
enabling complex post-training workflows like Reinforcement Learning from
Human Feedback (RLHF).

### The New Workload: RL/Post-Training Architecture

Post-training workflows introduce complex orchestration requirements:

```text
┌─────────────────────────────────────────────────────┐
│  RL / Post-Training System                          │
│                                                      │
│  ┌──────────────────┐         ┌──────────────────┐ │
│  │  Learning Alg.   │ ◄─────► │      Actor       │ │
│  │ (GRPO, PPO, ...) │         │                  │ │
│  │                  │         │  ┌──────────┐    │ │
│  │  Actor Update    │         │  │ Tools    │    │ │
│  └──────────────────┘         │  │ (Think,  │    │ │
│          ▲                    │  │ Terminal,│    │ │
│          │ Multi-turn         │  │ Browser) │    │ │
│          │ Rollouts +         │  └──────────┘    │ │
│          │ Rewards            │        │         │ │
│          │                    │        ▼         │ │
│  ┌───────┴───────┐           │  ┌──────────┐    │ │
│  │ VeRL Backend  │           │  │Env Runtime│   │ │
│  └───────────────┘           │  │ (SkyRL)  │    │ │
│                              │  └────┬─────┘    │ │
│                              │       │          │ │
│                              │       ▼          │ │
│                              │  Observation/    │ │
│                              │  Reward          │ │
│                              └──────────────────┘ │
│                                                    │
│                        Action → API Gateway        │
│                                      ▼             │
│                                 Sandbox Server     │
└────────────────────────────────────────────────────┘
```

**Components**:

- **Learning Algorithm**: GRPO, PPO, and other RL algorithms
- **Actor**: Makes decisions using tools (thinking, terminal, browser)
- **Environment Runtime**: Executes actions and provides feedback
- **VeRL Backend**: Coordinates multi-turn rollouts and rewards

This architecture requires sophisticated orchestration that Ray provides
naturally.

### Ray + Kubernetes: The Perfect Match

Ray and Kubernetes are co-evolving to support AI workloads:

**AI Infra Software Stack Requirements**:

```text
┌──────────────────────────────────────────────────┐
│ AI Workload (Post-training, Multimodal Data     │
│              Processing, Agentic AI, ...)        │
├──────────────────────────────────────────────────┤
│                                                  │
│    AI Infra Software Stack Challenges:          │
│                                                  │
│    • Scaling Compute & Heterogeneity            │
│    • Resource Management & Mixed CPU+GPU        │
│    • Many Data Modalities                       │
│    • Spot Instance Management                   │
│    • Scheduling & Dependency Management         │
│    • Hardware Failures                          │
│                                                  │
├──────────────────────────────────────────────────┤
│         Compute Substrate: GPUs, CPUs            │
└──────────────────────────────────────────────────┘
```

**How Ray and Kubernetes Complement Each Other**:

1. **Kubernetes provides**:
   - Container orchestration and lifecycle management
   - Resource allocation and node management
   - Service discovery and networking
   - Declarative infrastructure

2. **Ray provides**:
   - Distributed application framework
   - Actor model for stateful computation
   - Native Python APIs for ML workflows
   - Application-level scheduling and data sharing

3. **Together they enable**:
   - Seamless scaling from development to production
   - Efficient mixed CPU+GPU workload management
   - Fault tolerance for long-running AI training jobs
   - Integration with cloud-native observability

### Real-World Adoption

The PARK stack is being adopted by organizations worldwide:

- **Research Labs**: UC Berkeley's SkyRL for RL research
- **Tech Companies**: ByteDance's Verl, Alibaba's ROLL, Ant Group's AReaL
- **AI Startups**: Z.ai's SLIME for efficient post-training
- **Cloud Providers**: Support for Ray on Kubernetes across AWS, GCP, Azure

## The Future: PARK as the New Standard

Just as LAMP became synonymous with web infrastructure, PARK is emerging as
the standard for AI infrastructure:

- **PyTorch** provides the foundation for model development
- **AI algorithms** continue to advance rapidly
- **Ray** orchestrates complex distributed workflows
- **Kubernetes** manages the underlying infrastructure at scale

### Why PARK Matters

The PARK stack addresses the fundamental challenges of AI infrastructure:

1. **Unified Platform**: From research to production with consistent tooling
2. **Cloud-Native**: Leverages modern orchestration and observability
3. **Open Source**: Community-driven development and no vendor lock-in
4. **Production-Ready**: Battle-tested by major organizations at scale

## Conclusion

The transformation from SQL on CPUs to inference on GPUs represents a
fundamental shift in how we process data. This change is not just about
hardware - it's about supporting entirely new classes of applications that
work with multimodal data and require real-time inference.

The PARK stack (PyTorch + AI + Ray + Kubernetes) is emerging as the
foundational technology for this new era, with Ray serving as the critical
orchestration layer that connects AI frameworks with cloud-native
infrastructure. The co-evolution of vLLM + Ray and Ray + Kubernetes
demonstrates how the ecosystem is converging around proven patterns for
large-scale AI deployment.

As we move deeper into the AI era, understanding and adopting these patterns
will be essential for building scalable, efficient AI infrastructure.

---

## References

### PyTorchCon 2025 Presentation

- **Video**: "An Open Source Post-Training Stack: Kubernetes + Ray + PyTorch +
  vLLM" by Robert Nishihara, Anyscale (PyTorchCon 2025)

### Related Blog Posts

- [Inference Orchestration Solutions](../2025-12-01/inference-orchestration.md)
- [Training on Kubernetes Guide](../../training/README.md)
- [PyTorch Ecosystem Overview](../../training/pytorch-ecosystem.md)

### Projects and Frameworks

- [Ray](https://github.com/ray-project/ray) - Distributed computing framework
- [vLLM](https://github.com/vllm-project/vllm) - High-throughput LLM serving
- [PyTorch](https://pytorch.org/) - Machine learning framework
- [Kubernetes](https://kubernetes.io/) - Container orchestration

---

**Author**: AI Infrastructure Learning Path  
**Date**: December 15, 2025  
**Tags**: #ai-infrastructure #ray #vllm #pytorch #kubernetes #data-processing
