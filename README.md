# AI-Infra Landscape & Learning Path 🚀

Welcome to the **AI-Infra** repository! This project provides a curated landscape and structured learning path for engineers building and operating modern **AI infrastructure**, especially in the Kubernetes and cloud-native ecosystem.

## 🌐 Overview

This landscape visualizes key components across the AI Infrastructure stack, mapped by:

- **Horizontal Axis (X):** 
  - Left: Prototype / Early-stage projects
  - Right: Kernel & Runtime maturity

- **Vertical Axis (Y):**
  - Bottom: Infrastructure Layer (Kernel/Runtime)
  - Top: Application Layer (AI/Inference)

The goal is to demystify the evolving AI Infra stack and guide engineers on where to focus their learning.

## 📊 AI-Infra Landscape (2025)

> **Legend:**
> - Dashed outlines = Early stage or under exploration
> - Labels on right = Functional categories

![AI-Infra Landscape](./ai-infra-landscape.png)

## 🧭 Learning Path for AI Infra Engineers

### 📦 1. Kernel & Runtime (底层内核)
Core components for container and workload management.

- **Projects to Learn:**
  - `containerd`
  - `Kubernetes`
  - `KWOK` (K8s Workload on Kubernetes)
  - `CRI`, `CNI`, `CSI` basics

- **Learning Topics:**
  - Container lifecycle & runtime
  - Scheduler internals
  - Resource allocation & GPU management
  - Emulators & simulators (e.g. KWOK, Mocking Tools)

---

### 📍 2. Orchestration & Scheduling (调度与编排)

- **Projects to Learn:**
  - `Volcano`, `Kueue`
  - `LWS` (Lightweight Scheduler)
  - `Kai Scheduler`, `Godel`
  - `DRA` (Dynamic Resource Allocation)

- **Learning Topics:**
  - Job scheduling vs. pod scheduling
  - Binpack / Spread strategies
  - Queue management & SLOs
  - Multi-model & multi-tenant scheduling

---

### 🧠 3. Model Inference & Runtime Optimization (推理优化)

- **Projects to Learn:**
  - `vLLM`, `SGL`, `llm-d`
  - `kubeRay`, `AIBrix`, `Dynamo`

- **Learning Topics:**
  - Efficient transformer inference
  - CUDA Graphs, KV Cache, Paged KV, FlashAttention
  - LLM serving stacks
  - Multi-accelerator orchestration

---

### 🧰 4. Cloud Native Inference Stack (云原生推理)

- **Projects to Learn:**
  - `KServe`, `Knative`, `Istio`
  - `Model Spec`, `ImageVolume`

- **Learning Topics:**
  - Serverless model deployment
  - Inference service mesh
  - Model versioning & rollout strategies

---

### 🧩 5. AI Gateway & Workflow

- **Projects to Learn:**
  - `AI Gateway`, `LLM Gateway`
  - `Argo`, `Kubeflow`, `Metaflow` (optional)

- **Learning Topics:**
  - API orchestration for LLMs
  - Prompt routing and A/B testing
  - RAG workflows, vector DB integration

---

## 🔭 Coming Soon

- ✅ Hands-on labs with `kind`, `kwok`, and `vLLM`
- 📦 Helm charts & deploy examples
- 🎓 Weekly learning challenges & case studies

---

## 🤝 Contributing

We welcome contributions to improve this landscape and path! Whether it's a new project, learning material, or diagram update — please open a PR or issue.

## 📜 License

Apache License 2.0.

---

_This repo is inspired by the rapidly evolving AI Infra stack and aims to help engineers navigate and master it._

