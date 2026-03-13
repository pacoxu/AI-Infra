---
status: Active
maintainer: pacoxu
last_updated: 2026-03-03
tags: roadmap, planning, future-work, ai-native
---

# AI-Infra RoadMap 🗺️

This document outlines upcoming features, topics under consideration, and items
that may be out of scope for the AI-Infra repository. The roadmap helps guide
the evolution of this learning resource and sets expectations about future
content.

## 🌅 AI Native Era: The Second Half of Cloud Native (2025–2035)

The Cloud Native journey can be divided into two phases:

- **First Half (2015–2025)**: Focused on containers, microservices, and
  application delivery
- **Second Half (2025–2035)**: Focused on AI Native platform engineering,
  where models, agents, and inference workloads become first-class citizens

idea from https://mp.weixin.qq.com/s/di2HEsjLoCO4NB2Act6Qmg

### Key Paradigm Shifts

| Dimension | First Half (2015–2025) | Second Half (2025–2035, AI Native) |
| --- | --- | --- |
| Core Objects | Containers, Pods, Microservices | Models, Inference Tasks, Agents, Data Pipelines |
| Platform Goal | Stable application delivery | Continuous, efficient AI workload & Agent orchestration |
| Abstraction Layer | Deployment / Service / Ingress / Job | Model / Endpoint / Graph / Policy / Agent |
| Resource Scheduling | CPU / Memory / Node | GPU / TPU / ASIC / KV Cache / Bandwidth / Power |
| Engineering Focus | DevOps / GitOps / Platform Engineering 1.0 | AI Native Platform Engineering / AI SRE |
| Security & Compliance | Image security, CVE, Supply chain SBOM | Model security, Data security, AI supply chain & "hallucination dependencies" |
| Runtime Forms | Container + VM + Serverless | Container + WASM + Nix + Agent Runtime |

### AI Native Focus Areas

This repository is evolving to address the key challenges of the AI Native era:

| Direction | Technical Focus | Essential Difference from First Half |
| --- | --- | --- |
| **AI Native Platform** | Model/Agent as first-class citizens, unified abstraction & governance | Objects shift from services to models and inference |
| **Resource Scheduling** | DRA, heterogeneous computing, topology awareness, power & cost optimization | From static quotas to dynamic, policy-driven allocation |
| **Runtime** | Container + WASM + Nix + Agent Runtime | From "process containerization" to "execution graph containerization" |
| **Platform Engineering** | IDP + AI SRE + Security + Cost + Compliance | From tool assembly to "autonomous platforms" |
| **Security & Supply Chain** | Full-chain governance of LLM dependencies, model weights, datasets, vector DBs | Protected assets expand from images to "all AI engineering assets" |
| **Open Source & Ecosystem** | Upstream collaboration in AI Infra / Model Runtime / Agent Runtime | Not just "using open source" but "building the future in open source" |

## 🚀 Coming Soon

The following topics are planned for future addition to the repository,
organized by AI Native focus areas:

### AI Native Platform

- **Model/Agent Abstraction Patterns**: How to treat models and agents as
  first-class Kubernetes citizens, including CRD design patterns
- **Unified Model Governance**: Best practices for model versioning, rollout
  strategies, and multi-model orchestration

### Resource Scheduling

- **DRA updates**: New Dynamic Resource Allocation implementations like
  [dranet](https://github.com/google/dranet)
- **Heterogeneous Computing**: Multi-accelerator scheduling across GPU, TPU,
  NPU, and custom ASICs
- **Topology-Aware Scheduling**: GPU/network topology optimization for
  distributed training and inference
- **Power & Cost Optimization**: Energy-aware scheduling and cost models for
  AI workloads
- **Kueue + HAMi Integration**: Cloud-native GPU resource scheduling combining
  [Kueue](https://github.com/kubernetes-sigs/kueue) batch scheduling with
  [HAMi](https://github.com/Project-HAMi/HAMi) GPU sharing/isolation —
  reference: [ForceInjection Kueue+HAMi](https://github.com/ForceInjection/AI-fundermentals/blob/main/04_cloud_native_ai_platform/k8s/Kueue%20+%20HAMi.md)
- **NVIDIA Container Toolkit internals**: Deep dive into the underlying
  mechanisms of NVIDIA Container Toolkit for containerized GPU support —
  reference: [ForceInjection NVIDIA Container Toolkit](https://github.com/ForceInjection/AI-fundermentals/blob/main/04_cloud_native_ai_platform/k8s/Nvidia%20Container%20Toolkit%20%E5%8E%9F%E7%90%86%E5%88%86%E6%9E%90.md)
- **NVIDIA K8s Device Plugin analysis**: Architecture and implementation
  details of the NVIDIA Kubernetes device plugin —
  reference: [ForceInjection Device Plugin](https://github.com/ForceInjection/AI-fundermentals/blob/main/04_cloud_native_ai_platform/k8s/nvidia-k8s-device-plugin-analysis.md)

### GPU OS (Virtualization & Profiling)

GPU-level virtualization, resource partitioning, and profiling tools for
optimizing GPU utilization and debugging performance bottlenecks.

#### GPU Virtualization

- **MIG (Multi-Instance GPU)**: Partitioning a single GPU into multiple
  isolated instances for multi-tenant workloads
- **vGPU / SR-IOV**: Sharing GPUs across multiple VMs/containers via
  virtualization technologies
- **CUDA MPS (Multi-Process Service)**: Enabling concurrent multi-process
  execution on a single GPU to improve utilization

#### GPU Profiling / Instrumentation / Monitoring

- **Nsight Systems**: End-to-end timeline profiling (CPU↔GPU, kernel launch,
  communication/IO overlap)
- **Nsight Compute**: Per-kernel metrics (occupancy, memory bandwidth, warp
  efficiency, etc.)
- **CUPTI**: Low-level interface for collecting GPU events and performance
  counters
- **NVTX (NVIDIA Tools Extension)**: Code annotation/range markers to improve
  Nsight readability and phase alignment

### Kernels & Operator Optimization

GPU kernel development, optimization tools, and high-performance operator
libraries for AI workloads, fully leveraging hardware capabilities across GPU
generations.

#### Kernel DSL & Codegen

- **[Triton (triton-lang)](https://github.com/triton-lang/triton)**: Custom GPU
  kernel DSL and compiler for writing high-performance kernels in Python
- **[tilelang](https://github.com/tile-ai/tilelang)**: DSL targeting
  high-performance kernel development

#### Transformer Kernels

- **[FlashInfer](https://github.com/flashinfer-ai/flashinfer)**: High-performance
  inference-side kernels (attention, MoE, etc.)
- **[FlashAttention](https://github.com/Dao-AILab/flash-attention)**: Classic
  memory-efficient attention kernel
- **[xFormers](https://github.com/facebookresearch/xformers)**: Optimized
  transformer building blocks and related kernels

#### Math Primitives

- **[CUTLASS](https://github.com/NVIDIA/cutlass)**: GEMM and operator
  infrastructure from NVIDIA
- **[DeepGEMM](https://github.com/deepseek-ai/DeepGEMM)**: High-performance
  GEMM implementations and exploration from DeepSeek

#### Quantization & Low-Precision

- **[bitsandbytes](https://github.com/bitsandbytes-foundation/bitsandbytes)**:
  Low-bit training and inference toolchain
- **GPTQ / AWQ**: Post-training quantization approaches for inference
- **[AMD Quark](https://quark.docs.amd.com/)**: AMD ecosystem model optimization
  and quantization toolchain
- **[LLM Compressor](https://github.com/vllm-project/llm-compressor)**:
  Compression and quantization toolchain for LLMs (vLLM project)
- **[NVIDIA ModelOpt](https://github.com/NVIDIA/TensorRT-Model-Optimizer)**:
  NVIDIA ecosystem model optimization and quantization toolchain

### Distributed Communication (NCCL / UCX / Gloo)

Collective communication libraries and high-performance networking frameworks
for distributed training and inference.

- **[NCCL](https://github.com/NVIDIA/nccl)**: Core GPU collective communication
  library (AllReduce, AllGather, etc.) — the backbone of distributed training
- **[UCX](https://github.com/openucx/ucx)**: High-performance communication
  framework supporting RDMA, shared memory, and network protocols
- **[Gloo](https://github.com/facebookincubator/gloo)**: Collective
  communication library commonly used in the PyTorch ecosystem

### Runtime Evolution

- **Agent Runtime Environments**: Sandboxing and isolation patterns for AI
  agents (Agent Sandbox)
- **WASM for AI**: WebAssembly use cases in AI inference and edge deployments
- **Execution Graph Containerization**: Moving beyond process containerization
  to full inference DAG management

### Platform Engineering 2.0

- 🎓 **Weekly learning challenges & case studies**: Interactive learning
  materials to help engineers practice AI infrastructure concepts
- **Agentic Workflow development**: Deep dive into platforms like Dify, KAgent,
  or Dagger - [Issue #30](https://github.com/pacoxu/AI-Infra/issues/30)
- **AI SRE Practices**: Site reliability engineering adapted for AI workloads
- **Autonomous Platform Patterns**: Self-healing, auto-scaling, and
  self-optimizing AI infrastructure

### Hardware & Infrastructure

- **SuperNode architectures**: Coverage of large-scale AI hardware systems:
  - Huawei CloudMatrix 384 (UnifiedBus)
  - NVIDIA GB200 NVL72 (36 Grace CPUs + 72 Blackwell GPUs in rack-scale,
    liquid-cooled design)
  - 沐曦耀龙S8000 G2超节点 (Moffett YaoLong S8000 G2 SuperNode)

### Observability

- **Observability**: Advanced monitoring and metrics for AI workloads
  - eBPF for LLM (Deepflow)
  - AutoScaling Metrics and Strategies: TTFT, TPOT, ITL, etc.
  - [Issue #78](https://github.com/pacoxu/AI-Infra/issues/78)

### Inference Frameworks & Distributed Serving

- **llm-d**: Cloud-native high-performance distributed LLM inference framework
  based on Kubernetes — reference:
  [ForceInjection llm-d intro](https://github.com/ForceInjection/AI-fundermentals/blob/main/04_cloud_native_ai_platform/k8s/llm-d-intro.md)
- **vLLM + LWS multi-node inference**: Using LeaderWorkerSet (LWS) controller
  for multi-node, multi-GPU inference deployments on Kubernetes — reference:
  [ForceInjection LWS intro](https://github.com/ForceInjection/AI-fundermentals/blob/main/04_cloud_native_ai_platform/k8s/lws_intro.md)

### RL & Alignment (Post-Training / RLHF)

Reinforcement Learning from Human Feedback (RLHF) and post-training alignment
frameworks for large language models.

- **[verl](https://github.com/volcengine/verl)**: RL training system framework
  for LLMs, featuring flexible rollout backends (vLLM/SGLang) — ByteDance /
  VolcEngine
- **[SLIME](https://github.com/THUDM/SLIME)**: RL scaling framework designed
  for LLM post-training — THUDM
- **[OpenRLHF](https://github.com/OpenRLHF/OpenRLHF)**: Open-source RLHF
  training framework with support for PPO, DPO, and GRPO
- **[TRL](https://github.com/huggingface/trl)**: PPO/DPO and other alignment
  trainers in the HuggingFace ecosystem

### KV Cache Deep Dives

- **Mooncake architecture**: Detailed analysis of the KV-cache-centric LLM
  inference system design — reference:
  [ForceInjection Mooncake architecture](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/kv_cache/mooncake_architecture.md)
- **LMCache detailed analysis**: Source-level deep dive into LMCache covering
  its four-layer storage architecture (L1-L4), connector, engine, storage
  backends, controller, server, CacheBlend, and CacheGen — references:
  - [LMCache overview](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/kv_cache/lmcache/lmcache_overview.md)
  - [LMCacheConnector](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/kv_cache/lmcache/lmcache_connector.md)
  - [LMCacheEngine](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/kv_cache/lmcache/lmcache_engine.md)
  - [CacheBlend](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/kv_cache/lmcache/cache_blend.md)
  - [CacheGen](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/kv_cache/lmcache/cachegen.md)
- **Alibaba Cloud Tair KVCache**: Enterprise-grade centralized KVCache
  management system design and comparison with LMCache — reference:
  [ForceInjection Tair KVCache](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/kv_cache/ali_tair_kvcache/tair-kvcache-architecture-design.md)
- **vLLM KV Offloading vs LMCache**: Architecture comparison covering storage
  hierarchy and cross-instance sharing capabilities — reference:
  [ForceInjection KV Offloading analysis](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/kv_cache/kv_offloading_analysis.md)

### Storage & Checkpoint IO

High-performance distributed file systems and tensor serialization formats for
training checkpoints and model weights.

#### Distributed File Storage

- **[3FS (Fire-Flyer File System)](https://github.com/deepseek-ai/3FS)**:
  High-performance distributed file storage optimized for AI training workloads,
  especially for high-concurrency random reads (model loading) and small
  file / metadata IO — from DeepSeek

#### Checkpoint / Tensor IO

- **[safetensors](https://github.com/huggingface/safetensors)**: Simple, safe
  tensor serialization format for model weights — zero-copy, no arbitrary code
  execution (HuggingFace)
- **[TensorStore](https://github.com/google/tensorstore)**: Library for
  reading/writing large multi-dimensional arrays and sharded checkpoints — Google

### Vector Databases

Vector database solutions for embedding storage, similarity search, and
retrieval-augmented generation (RAG) pipelines.

- **[Milvus](https://github.com/milvus-io/milvus)**: CNCF Incubating —
  open-source vector database built for scalable similarity search
- **[Qdrant](https://github.com/qdrant/qdrant)**: High-performance vector
  similarity search engine written in Rust
- **[Weaviate](https://github.com/weaviate/weaviate)**: Cloud-native vector
  database with built-in ML model integrations
- **[pgvector](https://github.com/pgvector/pgvector)**: Open-source vector
  similarity search extension for PostgreSQL
- **[FAISS](https://github.com/facebookresearch/faiss)**: Local vector index
  library optimized for dense similarity search — Meta

### Deployment Best Practices

- **DeepSeek-V3 MoE deployment on H20**: Deployment guide and SLO validation
  for DeepSeek-V3 MoE model with vLLM on H20 hardware — reference:
  [ForceInjection DeepSeek-V3 deployment](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/inference_solutions/deepseek_v3_moe_vllm_h20_deployment.md)
- **Qwen2-VL-7B on Huawei Ascend**: Deployment optimization for multimodal
  models on domestic Huawei Ascend hardware — reference:
  [ForceInjection Qwen2-VL Huawei](https://github.com/ForceInjection/AI-fundermentals/blob/main/09_inference_system/inference_solutions/qwen2_vl_7b_huawei.md)

### Model Optimization

- **Model Quantization**: Techniques for reducing model size and improving
  inference performance
- **A general/basic guide about LLM**: Covering LLM fundamentals, MoE
  architectures, Ollama, and related tools
- **GPU Architecture & CUDA Programming**: Hardware fundamentals, parallel
  computing principles, and performance optimization strategies for GPU-based
  AI workloads — reference:
  [ForceInjection AI Infra Course](https://github.com/ForceInjection/AI-fundermentals/blob/main/10_ai_related_course/ai_infra_course/%E5%85%A5%E9%97%A8%E7%BA%A7/%E8%AE%B2%E7%A8%BF.md)

### LLM Capability Evaluation

Tools and benchmarks for evaluating LLM quality across dimensions including
knowledge, reasoning, code, instruction following, factuality, safety,
multilingual capabilities, and RAG quality.

#### Evaluation Frameworks

- **[lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)**:
  General-purpose evaluation framework with broad task coverage and unified
  reporting — EleutherAI
- **[OpenCompass](https://github.com/open-compass/opencompass)**: One-stop
  evaluation system with rich task sets, suitable for building internal
  evaluation platforms
- **[HELM](https://github.com/stanford-crfm/helm)**: Holistic evaluation
  framework with comprehensive metric dimensions — Stanford CRFM
- **[AlpacaEval](https://github.com/tatsu-lab/alpaca_eval)**: Automated
  pairwise evaluation for instruction following and dialogue quality
- **[FastChat / MT-Bench](https://github.com/lm-sys/FastChat)**: Dialogue
  evaluation scripts and benchmarks widely used by the community
- **[lighteval](https://github.com/huggingface/lighteval)**: Lightweight
  evaluation framework (HuggingFace), flexible for CI integration
- **[EvalPlus](https://github.com/evalplus/evalplus)**: Enhanced code evaluation
  extending HumanEval with stricter test cases and judging
- **[SWE-bench](https://github.com/swe-bench/SWE-bench)**: Real-world software
  engineering task repair benchmark and toolchain
- **[Ragas](https://github.com/explodinggradients/ragas) /
  [TruLens](https://github.com/truera/trulens) /
  [DeepEval](https://github.com/confident-ai/deepeval)**: RAG and application
  pipeline quality evaluation tools

#### Key Benchmarks

| Category | Benchmarks |
| --- | --- |
| **Knowledge & Language** | MMLU / MMLU-Pro, ARC (Easy/Challenge), HellaSwag, WinoGrande, TruthfulQA, PIQA / OpenBookQA |
| **Reasoning & Math** | GSM8K, MATH, BBH (Big-Bench Hard) / Big-Bench, AIME |
| **Code** | HumanEval / MBPP, EvalPlus, SWE-bench, LiveCodeBench |
| **Instruction & Chat** | MT-Bench (FastChat), AlpacaEval, IFEval |
| **Factuality / Hallucination** | TruthfulQA, FEVER, FactScore |
| **Safety & Robustness** | AdvBench, HarmBench, Do-Not-Answer, RealToxicityPrompts / ToxiGen |
| **Multilingual** | XNLI, XQuAD / TyDiQA, MIRACL / BEIR (retrieval) |
| **Retrieval / RAG QA** | HotpotQA / 2WikiMultihopQA / MuSiQue, NaturalQuestions / TriviaQA, BEIR |

### Security & Supply Chain

- **LLM Security & Compliance/Policy**: Security best practices and policy
  enforcement for LLM deployments
- **AI Supply Chain Security**: Model weight provenance, dataset governance,
  and "hallucination dependency" management
- **Vector Database Security**: Security patterns for embedding stores and
  retrieval systems

### Agent Communication

- **MCP and A2A**: Model Context Protocol and Agent-to-Agent communication -
  [Issue #32](https://github.com/pacoxu/AI-Infra/issues/32)

### Typical End-to-End Stack Architectures

Reference architectures combining layers across the AI Native stack for common
large-scale AI workloads:

#### Large-Scale Pre-Training / Fine-Tuning

GPU OS (MIG / Profiling) → Distributed Communication (NCCL + K8s / Slurm) →
PyTorch + Megatron-LM / DeepSpeed / FSDP → Storage (3FS) + Checkpoint IO
(safetensors / TensorStore)

#### Post-Training / RLHF

PyTorch → TRL / verl / OpenRLHF / SLIME → rollout backend (SGLang / vLLM) →
K8s + Ray (KubeRay)

#### Large-Scale Online Inference (Engine to Cluster)

Weights / Models (3FS) → Engine (vLLM / TensorRT-LLM / SGLang) → Serving
(KServe / Ray Serve / Triton Inference Server / BentoML) → Gateway / Routing
(SGLang Router / AIBrix) → Control Plane (llm-d / NVIDIA Dynamo) → KV Cache
(LMCache) → Kernel Acceleration (Triton / tilelang / FlashInfer / FlashAttention
/ CUTLASS / DeepGEMM)

## 🚫 Out of Scope

The following topics are currently considered out of scope for this repository.
They may be valuable but are either too broad, covered extensively elsewhere,
or don't align closely with the repository's focus on Kubernetes-based AI
infrastructure:

- **General Observability Projects**: Tools like Prometheus, Grafana,
  OpenTelemetry, etc. (These are well-documented elsewhere and not
  AI-specific)
- **RAG**: Retrieval-Augmented Generation architectures and implementations

## 💬 Discussion & Contributions

For some topics, we may open dedicated issues for discussion before deciding
whether to include them. If you have suggestions for new topics or want to
contribute learning materials, please:

- Open an issue to discuss the topic
- Check existing issues for ongoing discussions
- Submit a pull request with new content that aligns with the repository's
  focus

## 📅 Update Schedule

**This roadmap is reviewed and updated every quarter** to ensure it remains
current with the rapidly evolving AI infrastructure landscape. The next
scheduled review is planned for Q1 2026.

If you notice that items on this roadmap have become outdated or if you'd like
to propose new topics, please open an issue or submit a pull request.

---

Last updated: 2026-03-03
