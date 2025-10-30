---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: roadmap, planning, future-work
---

# AI-Infra RoadMap 🗺️

This document outlines upcoming features, topics under consideration, and items
that may be out of scope for the AI-Infra repository. The roadmap helps guide
the evolution of this learning resource and sets expectations about future
content.

## 🚀 Coming Soon

The following topics are planned for future addition to the repository:

- 🎓 **Weekly learning challenges & case studies**: Interactive learning
  materials to help engineers practice AI infrastructure concepts
- **Agentic Workflow development**: Deep dive into platforms like Dify, KAgent,
  or Dagger - [Issue #30](https://github.com/pacoxu/AI-Infra/issues/30)
- **SuperNode architectures**: Coverage of large-scale AI hardware systems:
  - Huawei CloudMatrix 384 (UnifiedBus)
  - NVIDIA GB200 NVL72 (36 Grace CPUs + 72 Blackwell GPUs in rack-scale,
    liquid-cooled design)
  - 沐曦耀龙S8000 G2超节点 (Moffett YaoLong S8000 G2 SuperNode)
- **DRA updates**: New Dynamic Resource Allocation implementations like
  [dranet](https://github.com/google/dranet)
- **Observability**: Advanced monitoring and metrics for AI workloads
  - eBPF for LLM (Deepflow)
  - AutoScaling Metrics and Strategies: TTFT, TPOT, ITL, etc.
  - [Issue #78](https://github.com/pacoxu/AI-Infra/issues/78)
- **Model Quantization**: Techniques for reducing model size and improving
  inference performance
- **LLM Security & Compliance/Policy**: Security best practices and policy
  enforcement for LLM deployments
- **A general/basic guide about LLM**: Covering LLM fundamentals, MoE
  architectures, Ollama, and related tools
- **MCP and A2A**: Model Context Protocol and Agent-to-Agent communication -
  [Issue #32](https://github.com/pacoxu/AI-Infra/issues/32)

## 🚫 Out of Scope

The following topics are currently considered out of scope for this repository.
They may be valuable but are either too broad, covered extensively elsewhere,
or don't align closely with the repository's focus on Kubernetes-based AI
infrastructure:

- **Wasm**: WebAssembly for AI workloads
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

Last updated: 2025-10-29
