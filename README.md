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
  - [`Kubernetes`](https://github.com/kubernetes/kubernetes): CNCF First Graduated Project, Core.
  - [`CRI`](https://github.com/kubernetes/cri-api)
    - [`containerd`](https://github.com/containerd/containerd): Container Runtime.
    - [`KubeVirt`](https://github.com/kubevirt/kubevirt): Kubernetes SIG Project for running VMs in Kubernetes.
    - 
  - [`CNI`](https://github.com/containernetworking/cni)
  - [`CSI`](https://github.com/container-storage-interface/spec)
  - [`KWOK`](https://github.com/kubernetes-sigs/kwok): Kubernetes SIG Project for mock testing(especially for GPU nodes).
  - [`Helm`](https://github.com/helm/helm): Package Manager for Kubernetes.

- **Learning Topics:**
  - Container lifecycle & runtime
  - Scheduler internals
  - Resource allocation & GPU management
  - Emulators & simulators (e.g. KWOK, Mocking Tools)

---

### 📍 2. Orchestration & Scheduling (调度与编排)

- **Projects to Learn:**
  - Scheduling(Include [Batch, Kubernetes-WG](https://github.com/kubernetes/community/blob/master/wg-batch/README.md)):
    - [`Kueue`](https://github.com/kubernetes-sigs/kueue): Kubernetes Subproject
    - [`Volcano`](https://github.com/volcano-sh/volcano): CNCF Incubating
    - [`koordinator`](https://github.com/koordinator-sh/koordinator): CNCF Sandbox
    - [`Godel Scheduler`](https://github.com/kubewharf/godel-scheduler)
    - [`HAMI`](https://github.com/Project-HAMi/HAMi): CNCF Sandbox
    - [`NVIDIA Kai Scheduler`](https://github.com/NVIDIA/kai-scheduler)
    - [`Apache YuniKorn`](https://github.com/apache/yunikorn-core)
  - Workloads(Pod Group):
    - [`LWS`](https://github.com/kubernetes-sigs/lws)
    - Pod Group & Gang Scheduling KEPs: See roadmap below.
  - Device Management([Kubernetes WG](https://github.com/kubernetes/community/blob/master/wg-device-management/README.md)):
    - [`DRA`](https://github.com/kubernetes/dynamic-resource-allocation/)
    - [`NRI`](https://github.com/containerd/nri)

- **Learning Topics:**
  - Job scheduling vs. pod scheduling
  - Binpack / Spread strategies
  - Queue management & SLOs
  - Multi-model & multi-tenant scheduling

- **RoadMap(Ongoing Proposals):**
  - Gang Scheduling Support in Kubernetes [#4671](https://github.com/kubernetes/enhancements/pull/4671)
    - LWS Gang Scheduling [KEP](https://github.com/kubernetes-sigs/lws/pull/496)

---

### 🧠 3. Model Inference & Runtime Optimization (推理优化)

- **Projects to Learn:**
  - engine:
    - [`vLLM`](https://github.com/vllm-project/vllm)
    - [`SGL`](https://github.com/superglue-ai/sgl)
    - [`Triton`](https://github.com/triton-inference-server/server)
    - [`Text Generation Inference`](https://github.com/huggingface/text-generation-inference)
  - inference platform:
    - [`llm-d`](https://github.com/llm-d/llm-d)
    - [`AIBrix`](https://github.com/aibrix/aibrix)
    - [`Dynamo`](https://github.com/dynamo/dynamo)
    - [`llmaz`](https://github.com/InftyAI/llmaz)
  - Others:
    - [`KServe`](https://github.com/kserve/kserve): CNCF Incubating

- **Learning Topics:**
  - Efficient transformer inference
  - CUDA Graphs, KV Cache, Paged KV, FlashAttention
  - LLM serving stacks
  - Multi-accelerator orchestration

- **RoadMap(Ongoing Proposals Or Working Groups):**
  - [Serving WG](https://github.com/kubernetes/community/blob/master/wg-serving/README.md)

---

### 🧰 4. Cloud Native Inference Stack (云原生推理)

- **Projects to Learn:**
  - [`KServe`](https://github.com/kserve/kserve), [`Knative`](https://github.com/knative/serving), [`Istio`](https://github.com/istio/istio)
  - [`Model Spec`](https://github.com/modelpack/model-spec), [`ImageVolume`]( https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/4639-oci-volume-source)

- **Learning Topics:**
  - Serverless model deployment
  - Inference service mesh
  - Model versioning & rollout strategies

---

### 🧩 5. AI Gateway & Agentic Workflow

- **Projects to Learn:**
  - AI Gateway:
    - [`Envoy AI Gateway`](https://github.com/envoyproxy/ai-gateway)
    - [`Gateway API Inference Extension`](https://github.com/kubernetes-sigs/gateway-api-inference-extension)
    - [`KGateway`](https://github.com/kgateway-dev/kgateway): previously known as Gloo.
    - [`DaoCloud knoway`](https://github.com/knoway-dev/knoway)
  - CD:
    - [`Argo`](https://github.com/argoproj/argo): CNCF Graduated
    - [`Kubeflow`](https://github.com/kubeflow/kubeflow): CNCF Incubating
    - [`Metaflow`](https://github.com/Netflix/metaflow) (optional)
  - Agentic Workflow:
    - [`Dify`](https://github.com/langgenius/dify)
    - [`KAgent`](https://github.com/kagent-dev/kagent): CNCF Sandbox
    - [`Dagger`](https://github.com/dagger/dagger)

- **Learning Topics:**
  - API orchestration for LLMs
  - Prompt routing and A/B testing
  - RAG workflows, vector DB integration

---

## 🔭 Coming Soon & Something that may not be included

For some reasons, some topics may not be included in this repo, but I may open some issues to discuss them and add some learning materials there.

Coming Soon:

- 🎓 Weekly learning challenges & case studies
- AI Gateway details: Gateway API Inference Extension
- Parallelism & Caching
- Agentic Workflow development like Dify
- KAgent or Dagger
- AutoScaling Metrics and Strategies: TTFT, TPOT, ITL, etc.
- SuperNode
- Devices: RDMA, etc.
- Observability: eBPF for LLM(Deepflow)
- Model Quantization
- LLM Security & Compliance/Policy
- A general/basic guide about LLM, MoE, Ollama, etc.

Something that may not be included:

- Training
- Wasm
- MCP related and A2A
- General Observability Projects: Prometheus, Grafana, OpenTelemetry, etc.

## 🤝 Contributing

We welcome contributions to improve this landscape and path! Whether it's a new project, learning material, or diagram update — please open a PR or issue.

## 📚 References

- [CNCF Landscape](https://landscape.cncf.io/)
- [Awesome LLMOps](https://awesome-llmops.inftyai.com/)
- [CNCF TAG Workloads Foundation](https://github.com/cncf/toc/blob/main/tags/tag-workloads-foundation/README.md)
- [CNCF TAG Infrastructure](https://github.com/cncf/toc/blob/main/tags/tag-infrastructure/README.md)
- [CNCF AI Initiative](https://github.com/cncf/toc/issues?q=is%3Aissue%20state%3Aopen%20label%3Akind%2Finitiative)
- Kubernetes SIG Network [AI Gateway Working Group](https://groups.google.com/a/kubernetes.io/g/steering/c/6VZdzwg4OqI/m/PKXCDtfRBQAJ?utm_medium=email&utm_source=footer):

## 📜 License

Apache License 2.0.

---

_This repo is inspired by the rapidly evolving AI Infra stack and aims to help engineers navigate and master it._

