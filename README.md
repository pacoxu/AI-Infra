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

**Legend:**

> - Dashed outlines = Early stage or under exploration
> - Labels on right = Functional categories

![AI-Infra Landscape](./ai-infra-landscape.png)

## 🧭 Learning Path for AI Infra Engineers

### 📦 1. Kernel & Runtime (底层内核)

Core components for container and workload management.

- **Projects to Learn:**
  - [`containerd`](https://github.com/containerd/containerd)
  - [`Kubernetes`](https://github.com/kubernetes/kubernetes)
  - [`KWOK`](https://github.com/kubernetes-sigs/kwok)
  - [`CRI`](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/runtime-class.md), [`CNI`](https://github.com/containernetworking/cni), [`CSI`](https://github.com/container-storage-interface/spec)

- **Learning Topics:**
  - Container lifecycle & runtime
  - Scheduler internals
  - Resource allocation & GPU management
  - Emulators & simulators (e.g. KWOK, Mocking Tools)

---

### 📍 2. Orchestration & Scheduling (调度与编排)

- **Projects to Learn:**
  - [`Volcano`](https://github.com/volcano-sh/volcano), [`Kueue`](https://github.com/kueue/kueue)
  - [`LWS`](https://github.com/lws-team/lws), [`Kai Scheduler`](https://github.com/kai-scheduler/kai-scheduler), [`Godel`](https://github.com/godel/godel)
  - [`DRA`](https://github.com/dynamic-resource-allocation/dra)

- **Learning Topics:**
  - Job scheduling vs. pod scheduling
  - Binpack / Spread strategies
  - Queue management & SLOs
  - Multi-model & multi-tenant scheduling

---

### 🧠 3. Model Inference & Runtime Optimization (推理优化)

- **Projects to Learn:**
  - [`vLLM`](https://github.com/vllm-project/vllm), [`SGL`](https://github.com/superglue-ai/sgl), [`llm-d`](https://github.com/llm-d/llm-d)
  - [`kubeRay`](https://github.com/kubeflow/kuberay), [`AIBrix`](https://github.com/aibrix/aibrix), [`Dynamo`](https://github.com/dynamo/dynamo)

- **Learning Topics:**
  - Efficient transformer inference
  - CUDA Graphs, KV Cache, Paged KV, FlashAttention
  - LLM serving stacks
  - Multi-accelerator orchestration

---

### 🧰 4. Cloud Native Inference Stack (云原生推理)

- **Projects to Learn:**
  - [`KServe`](https://github.com/kserve/kserve), [`Knative`](https://github.com/knative/serving), [`Istio`](https://github.com/istio/istio)
  - [`Model Spec`](https://github.com/kserve/model-spec), [`ImageVolume`](https://github.com/kserve/image-volume)

- **Learning Topics:**
  - Serverless model deployment
  - Inference service mesh
  - Model versioning & rollout strategies

---

### 🧩 5. AI Gateway & Workflow

- **Projects to Learn:**
  - [`AI Gateway`](https://github.com/ai-gateway/ai-gateway), [`LLM Gateway`](https://github.com/llm-gateway/llm-gateway)
  - [`Argo`](https://github.com/argoproj/argo), [`Kubeflow`](https://github.com/kubeflow/kubeflow), [`Metaflow`](https://github.com/Netflix/metaflow) (optional)

- **Learning Topics:**
  - API orchestration for LLMs
  - Prompt routing and A/B testing
  - RAG workflows, vector DB integration

---

## 🔭 Coming Soon

- 🎓 Weekly learning challenges & case studies

---

## 🤝 Contributing

We welcome contributions to improve this landscape and path! Whether it's a new project, learning material, or diagram update — please open a PR or issue.

## 📜 License

Apache License 2.0.

---

_This repo is inspired by the rapidly evolving AI Infra stack and aims to help engineers navigate and master it._

