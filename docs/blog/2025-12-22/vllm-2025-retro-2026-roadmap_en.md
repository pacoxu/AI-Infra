---
status: Active
maintainer: pacoxu
last_updated: 2025-12-22
tags: vllm, llm, inference, roadmap, ai-infrastructure
---

# vLLM 2025 Retrospective & 2026 Roadmap

This article summarizes vLLM's achievements in 2025 and outlines the vision
for 2026. Content is based on vLLM Office Hours #38 (December 18, 2024),
presented by vLLM Project Maintainer Simon Mo (UC Berkeley) and vLLM Core
Committee member Michael Goin (Red Hat AI).

**Note:** Some content was generated with AI assistance. Please verify before
using in production.

## Table of Contents

- [vLLM Project Overview](#vllm-project-overview)
- [2025 Growth Highlights](#2025-growth-highlights)
- [API Evolution: Towards Agentic & RL](#api-evolution-towards-agentic--rl)
- [Model Ecosystem: SOTA Model Support](#model-ecosystem-sota-model-support)
- [Engine Revamp: V1 Core Architecture](#engine-revamp-v1-core-architecture)
- [Hardware Ecosystem: Diversity and Frontier](#hardware-ecosystem-diversity-and-frontier)
- [Distributed: Scale Out & Usability](#distributed-scale-out--usability)
- [State of vLLM 2025](#state-of-vllm-2025)
- [2026 Focus Areas](#2026-focus-areas)
- [Get Involved](#get-involved)
- [References](#references)

## vLLM Project Overview

vLLM is the industry-leading high-throughput and memory-efficient inference
and serving engine for LLMs.

### Core Metrics

- GitHub Stars: 65K+
- Monthly PRs: 800+
- GPUs deployed 24/7: 500K+
- Active Members: 10K+
- Slack Community: slack.vllm.ai

### Project Milestones

- **2000+ contributors** from over **50 major companies**
- Support for **100+ model architectures**
- Flexible device parallelism capabilities:
  - Tensor Parallel
  - Expert Parallel
  - Data Parallel
  - Context Parallel
  - Disaggregated Prefill/Decode
  - Disaggregated Encoder

## 2025 Growth Highlights

### User Growth

- Q1/Q2: Usage growth of **80%**
- Q3: Usage growth of **30%**

**Note:** This is a small biased subset that did not opt-out of usage data
reporting.

### Model Distribution

Among models served by vLLM, **Qwen series has a very high proportion**,
followed by Llama, Mistral, Gpt-OSS, and DeepSeek series.

### Hardware Distribution

Current hardware support is dominated by NVIDIA GPUs, with AMD hardware
accounting for only single-digit percentages. However, the community is
actively expanding support for more hardware platforms.

## API Evolution: Towards Agentic & RL

vLLM significantly expanded API capabilities in 2025 to support Agentic AI and
Reinforcement Learning scenarios.

### Core API Layers

#### 1. LLM Class

A Python interface for offline batched inference.

#### 2. OpenAI-Compatible Server

A FastAPI-based server for online serving, compatible with OpenAI API
standards.

#### 3. Universal Drop-in Compatible Server

- **Multi-Modality Input API**: Support for images, audio, and other inputs
- **Rerank, Pooling and Embedding API**: Support for text representation tasks
- **Responses API**: Structured responses
- **SageMaker API**: AWS integration
- **Anthropic API**: Claude model compatibility
- **API for RL**: Tokens-in-tokens-out interface
- **Omni Modality API** (WIP): Full modality support

#### 4. Native Support for Reinforcement Learning

vLLM is deeply integrated with multiple RL frameworks:

- verl
- PRIME-RL
- SkyRL
- unsloth
- OPENRLHF
- Pipeline RL
- NVIDIA Cosmos
- TRL
- AReaL
- RLinf
- Nemo RL
- ROLL

## Model Ecosystem: SOTA Model Support

### Broad Model Support

vLLM supports almost all popular text-generation models.

### Transformers Backend

- Supports models not in vLLM but runnable by Transformers
- Developers can write model implementations in Transformers
- Leverages vLLM's KV cache management and continuous batching
- Works for both vision and language models
- Performance on par with pure vLLM implementation

### vLLM Prioritizes Accuracy

vLLM places model inference accuracy first, ensuring generated results are
consistent with the original model.

### vLLM Prioritizes Performance

While ensuring accuracy, vLLM continuously optimizes inference performance.

### State-of-Art Vision Model Support

vLLM provides industry-leading support for vision-language multimodal models.

### Multi-Modality Trend in 2025

- More models are emerging with built-in multimodal understanding, without
  compromising their strength in text tasks
- Multimodal generation capabilities from open source models are getting
  better (Hunyuan Image 3.0, Qwen3-Omni, Qwen-Image-Edit, etc.)

## Engine Revamp: V1 Core Architecture

### vLLM V1: A Major Upgrade

**Release Date:** January 27, 2025

vLLM V1 is a major upgrade to the core architecture, addressing the challenge
of combining multiple inference optimization techniques.

### Key Challenge: How to Integrate & Combine Numerous Inference Optimizations?

#### Inference Optimizations in vLLM

**Scheduling-related Optimizations:**

- Prefix Caching
- Speculative Decoding
- Chunked Prefills
- Disaggregated Serving
- Streaming Prefills
- Jump-forward Decoding

**Others:**

- Quantization
- Cascade Attention
- Structured Outputs
- CPU KV Cache Offloading
- Multi-LoRA Serving

#### Problem: Combining Numerous Inference Optimizations Effectively

Theoretically, most inference optimization techniques are orthogonal, so they
can be combined together to maximize performance. However, we found this very
difficult in practice.

**Feature Matrix of vLLM V0:** Some features cannot work well together.

**In vLLM V1:** Almost all compatibilities between features are fixed.

### V1 Engine Highlights

vLLM V1 introduces several key improvements:

#### Hybrid Allocator

The hybrid allocator is a core innovation in the V1 engine, providing flexible
KV cache memory management to support the memory requirements of different
optimization techniques.

#### KV Connector

KV Connector provides flexible KV cache storage backends, supporting:

**Project Integration:**

- LMCache
- Mooncake
- llm-d

**Storage Backends:**

- CPU RAM
- Local Storage
- GDS Backend
- Redis
- InfiniStore
- Mooncake
- Valkey
- Weka

## Hardware Ecosystem: Diversity and Frontier

vLLM actively expands its hardware ecosystem through a plugin mechanism to
support multiple hardware platforms.

### vLLM Hardware Plugin Ecosystems

- **vLLM TPU** (Preview): Google TPU support
- **vllm-ascend**: Huawei Ascend NPU support
- **vllm-spyre**: Spyre AI accelerator support
- **vllm-neuron**: AWS Neuron support
- **vllm-gaudi**: Intel Gaudi AI accelerator support
- **vllm-metax**: MetaX hardware support
- **vllm-openvino**: Intel OpenVINO support

## Distributed: Scale Out & Usability

vLLM significantly improved large-scale deployment and distributed serving
capabilities in 2025.

### Large-Scale Serving Case Study

**DeepSeek Serving:** Achieved **2.2k tok/s** throughput on H200 GPUs using
Wide-EP (Wide Expert Parallel) architecture.

Reference blog:
blog.vllm.ai/2025/12/17/large-scale-serving.html

### vLLM Router

**vLLM Router** is a high-performance and Prefill/Decode aware load balancer,
providing intelligent traffic distribution for large-scale serving.

Reference blog:
blog.vllm.ai/2025/12/13/vllm-router-release.html

## State of vLLM 2025

vLLM achieved significant milestones in 2025:

- **Community Growth**: 2000+ contributors, 50+ major companies involved
- **Technical Breakthroughs**: V1 engine release, major feature compatibility
  improvements
- **Ecosystem Expansion**: Support for 100+ model architectures, multiple
  hardware platforms
- **Rich APIs**: Reinforcement learning, multimodal, multiple standard API
  support
- **Performance Optimization**: Large-scale serving cases, high-throughput
  deployments

## 2026 Focus Areas

vLLM will focus on three core directions in 2026:

### 1. Stability, Accuracy, Performance

Continue to improve engine stability, ensure inference accuracy, and optimize
performance.

### 2. Frontier Models

- Support for the latest SOTA model architectures
- Deep integration with reinforcement learning frameworks

### 3. Hardware Stability

Improve stability and performance across hardware platforms, expand hardware
ecosystem coverage.

## Get Involved

We welcome community members to participate in the vLLM project:

- **GitHub**: github.com/vllm-project/vllm
- **Slack Community**: slack.vllm.ai
- **Events**: vllm.ai/events (includes Office Hours and global vLLM Meetups)

## References

- vLLM Office Hours #38 Video:
  youtube.com/watch?v=-5n9_IxkLxo&list=PLbMP1JcGBmSHxp4-lubU5WYmJ9YgAQcf3
  &index=1
- vLLM Official Website: vllm.ai
- vLLM GitHub Repository: github.com/vllm-project/vllm
- vLLM Blog: blog.vllm.ai

---

*This article is compiled by the AI-Infra community. Feedback and
contributions are welcome.*
