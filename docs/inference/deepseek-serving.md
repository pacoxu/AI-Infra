---
status: Active
maintainer: pacoxu
last_updated: 2026-10-20
tags: inference, deepseek, deepinfer, protocol, serving
canonical_path: docs/inference/deepseek-serving.md
---

# DeepInfer and deepseek-recipe

[DeepInfer](https://github.com/deepseek-ai/DeepInfer) and
[deepseek-recipe](https://github.com/deepseek-ai/deepseek-recipe) are two
slices of DeepSeek's serving path, released as separate repositories. They do
not replace a Kubernetes inference platform. Together they cover the model
runtime and the API-to-prompt contract. The cache, disaggregated serving, and
replica routing around them are still platform work.

## Where they sit

This repository treats AI Infra as three loops: training, inference (prefill /
decode, KV cache, disaggregation, routing), and RL that has to keep training
and serving consistent. These two projects land in the inference loop, on
either side of the engine boundary:

| Layer | Project | What this release does | Neighbor in this landscape |
| --- | --- | --- | --- |
| API and gateway | — | HTTP, auth, rate limit, replica choice | [Gateway API Inference Extension](https://github.com/kubernetes-sigs/gateway-api-inference-extension), AIBrix Gateway, Kthena Router |
| Protocol adapter | [deepseek-recipe](https://github.com/deepseek-ai/deepseek-recipe) | Messages / Chat Completions / Responses ↔ conversation ↔ prompt and token ids | Sits in the API process; examples use mock inference |
| Engine | [DeepInfer](https://github.com/deepseek-ai/DeepInfer) | Offline inference: scheduler, sampler, parallelism, kernels | vLLM, SGLang, TensorRT-LLM |
| Serving system | Not in the DeepInfer release | KV cache, VE / prefill / decode disaggregation, DP load balancing | [Caching](./caching.md), [P/D disaggregation](./pd-disaggregation.md), [Grove](./grove.md), [Dynamo](./dynamo.md) |
| Kernels and collectives | Separate DeepSeek repos | Attention, GEMM, MoE dispatch, top-k | [Kernel section](./README.md#kernel-optimization-算子与内核优化) |
| Cluster placement | — | Gang scheduling, scale-up domain, device allocation | LWS, Grove, DRA, [SuperNode](../hardware/supernode.md) |

```text
Client / Agent
    │  Chat Completions, Responses, or Messages
    ▼
AI Gateway                 routing, auth, DP replica selection
    │
    ▼
deepseek-recipe            protocol ↔ conversation ↔ prompt / token ids
    │                      sampling params, output constraint
    ▼
DeepInfer                  scheduler, sampler, Attention DP / CP, MoE EP
    │
    ├── still required for a full service:
    │     KV cache, VE/prefill/decode disaggregation, DP load balancing
    ▼
FlashMLA · DeepGEMM · DeepEP · TileKernels · DeepSelect · TileLang
    ▼
NVIDIA SM100 or Huawei Ascend 950, inside one scale-up domain
```

DeepInfer's own README draws that line. A complete inference service still
needs a KV cache system, VE / prefill / decode disaggregation, and load
balancing across data-parallel replicas for both prefill and decode. Most of
the engine-side disaggregation functionality is already implemented; the
service around it is not part of this release. deepseek-recipe states the
matching boundary from above: the caller must provide model inference, tool
execution, and HTTP transport.

## DeepInfer

[DeepInfer](https://github.com/deepseek-ai/DeepInfer) is the high-performance
inference framework behind DeepSeek's large-scale production services. The
open-source drop (repository created 2026-10-16, Apache-2.0) is **offline
inference** for one model: DeepSeek-V4.1-Flash. The default checkpoint is
[`deepseek-ai/DeepSeek-V4.1-Flash-1017`](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017).

It was built primarily on [vLLM](https://github.com/vllm-project/vllm), with
additional ideas from SGLang and TensorRT-LLM. That lineage matters for AI
Infra: DeepInfer is a specialized engine, not a second orchestration
platform. vLLM and SGLang remain the general engines in this landscape;
DeepInfer is the DeepSeek-model path that exposes the production parallelism
and kernel choices directly.

### What the engine includes

| Feature | Role in the serving path |
| --- | --- |
| Optimized kernels | [FlashMLA](https://github.com/deepseek-ai/FlashMLA), [DeepGEMM](https://github.com/deepseek-ai/DeepGEMM), [DeepEP](https://github.com/deepseek-ai/DeepEP), [TileKernels](https://github.com/deepseek-ai/TileKernels), [DeepSelect](https://github.com/deepseek-ai/DeepSelect), plus in-tree TileLang kernels |
| Attention DP / balanced CP | Data-parallel attention and context parallelism that splits a batch evenly across CP units |
| MoE EP + EPLB | Expert parallelism with expert-parallel load balance. Redundant experts default to 32 and are rounded so the expert count divides `ep_size` |
| DSpark | Draft tokens plus confidence-scheduled verification. `DEEPINFER_ENABLE_MTP_VARLEN=1`; `DEEPINFER_USE_NEXTN_DECODE` sets the max draft length (default 5) |
| SWA bounded replay | Decoder prefill replays a bounded suffix instead of the full window. V4.1 defaults: `DEEPINFER_YOCO_PREFILL_TRUNCATION_MODE=compact`, `DEEPINFER_YOCO_PREFILL_KEEP_TOKENS=140` |
| Asynchronous scheduling | CPU batch scheduling overlaps device execution. On by default |
| Batch-invariant inference | Same results across batch compositions. `DEEPINFER_BATCH_INVARIANT=1`, NVIDIA only |
| Deterministic sampling | Same tokens and sampling params produce the same output. Batch-invariant mode, MTP varlen off, and a fixed `seq_seed`. NVIDIA only |
| Structured outputs | Regex, JSON schema, or EBNF via `SamplingParams.so_args` |

Published Pareto curves were measured on 4 SM100 GPUs for prefill and 64 for
decode, each inside one scale-up domain. That is a placement constraint, not
a Kubernetes feature: the communicating group has to land inside the scale-up
fabric. See [SuperNode](../hardware/supernode.md) for how those domains show
up on GB200 / Vera Rubin class racks and on domestic supernodes.

### Runtime boundary

Supported hardware in this release:

- NVIDIA SM100 (CUDA 13)
- Huawei Ascend 950 (CANN 9.2)

Host prerequisites: Linux, GCC >= 13, Python 3.12. Select the accelerator
before the build and keep it exported at runtime:

```bash
export DEEPINFER_ACCELERATOR=nvidia   # or ascend
./build.sh
python examples/offline_inference.py
```

Offline examples cover EP, attention DP, and CP (`--ep`, `--dp`, `--cp`).
Benchmarks decouple prefill and decode: prefill chunk size and non-cached
suffix length do not set the decode batch, and decode reuses the shared
prefix KV produced by prefill. Vision encoding can be swept on its own
(`prompt_mode=image`, encoder sweep) without loading the full LLM, which
matches the VE role in a disaggregated pipeline.

What you still build outside the process:

- **KV cache system.** The benchmark reuses a shared prefix inside one run.
  Cross-request, cross-node, or SSD-backed KV is a separate system. See
  [Caching](./caching.md).
- **VE / prefill / decode as a service.** The engine can split the work and
  already contains most of the required engine functionality. Turning that
  into separately scaled roles is the job of LWS, Grove, llm-d, Dynamo, or
  KServe. See [P/D disaggregation](./pd-disaggregation.md).
- **Load balancing across DP replicas**, for both prefill and decode. That is
  gateway and router work, not sampler work.

## deepseek-recipe

[deepseek-recipe](https://github.com/deepseek-ai/deepseek-recipe) (repository
created 2026-09-10, MIT, Rust with Python bindings; PyPI `0.2.0` on
2026-10-20) converts API requests into the conversation format DeepSeek models
expect, renders prompts, encodes token ids, and parses model output back into
the caller's protocol.

It is the contract between an API server and an inference backend. It does
not run the model, execute tools, or speak HTTP. `server-rs` (Axum) and
`server-py` (FastAPI) are examples with mock inference, so the protocol can
be developed without a GPU.

### What the adapter includes

- **Protocols:** Messages, Chat Completions, and Responses, including
  streaming and complete responses. Text, images, thinking mode, client tool
  calls, and Chat Completions `prefix` continuation.
- **Prompts:** DeepSeek V4 and V4.1 rendering, plus token encoding when a
  tokenizer is attached. Default model names are `DeepSeek-V4-Pro` and
  `DeepSeek-V4.1-Flash`; other names register through
  `ConversionOptions::with_model_alias`.
- **Generation settings:** thinking mode, reasoning effort, `temperature`,
  `top_p`, and output limits. If the request omits `max_tokens`, the default
  is 8192 outside thinking mode, 65536 in thinking mode, and 131072 in
  thinking mode with `max` effort, after the prompt is checked against the
  context limit.
- **Output parsing:** reasoning content, tool calls, JSON object output, and
  stop sequences. With a tokenizer attached, usage can report
  `reasoning_tokens`.
- **Structured output:** validates a JSON schema and writes it into the
  prompt, or passes a regex through as `ResponseFormat::Regex`. It selects
  the `OutputConstraint` on `InferenceOptions`. The backend decides whether
  to enforce that constraint. DeepInfer is one backend that can: its
  sampler accepts regex, JSON schema, and EBNF.
- **Images:** base64 or URLs, preprocessed for V4.1 with OpenCV. V4 does not
  accept images; each image becomes the text `[Unsupported Image]`. URL fetch
  connects to any address unless the service installs a `DestinationFilter`.
- **Tools:** function tools; Responses also has tool namespaces and the
  `apply_patch` custom tool. V4.1 supports deferred tool loading in Messages
  and client-executed tool search in Responses. The library does not call
  the tools.
- **Log probabilities:** request fields are copied into `InferenceOptions`.
  The caller fills `InferenceChunk::Tokens`. The library does not compute
  probabilities.

| Package | Purpose |
| --- | --- |
| `deepseek-recipe` | Protocol conversion and model-output parsing |
| `deepseek-recipe-core` | Conversation, message, image, and tool types |
| `deepseek-recipe-encoding` | V4 and V4.1 prompt rendering and token encoding |
| `deepseek-recipe-image` | Image fetch and preprocessing |
| `deepseek-recipe-python` | Python bindings, imported as `deepseek_recipe` |
| `encoding-decoding-demo` | Local web UI for prompt render and output parse |
| `server-rs` / `server-py` | API examples with mock inference |

Python 3.10+ installs the bindings with `pip install deepseek-recipe`. A
source build of the image path needs Rust, OpenCV 4.x, and libclang.

## How a request crosses the two

1. The gateway accepts a Chat Completions, Responses, or Messages request and
   picks a prefill or decode replica.
2. deepseek-recipe converts that body into a conversation, renders the V4 or
   V4.1 prompt, and optionally encodes token ids. It also resolves sampling
   defaults and the structured-output constraint.
3. The caller hands the prompt or token ids to an inference backend. With
   DeepInfer, that is `SamplingParams` (including `so_args` when the
   constraint should be enforced) on the offline engine, or the same engine
   behind a service the caller still has to operate.
4. DeepInfer runs kernels under Attention DP / CP and MoE EP, optionally with
   DSpark drafts and SWA bounded replay, and returns tokens.
5. deepseek-recipe parses those tokens into reasoning content, tool calls,
   and the response schema the client asked for. Tool execution, if any,
   happens in the agent runtime after that parse.

Step 2 and step 5 are CPU work and belong next to the API process. Step 4 is
GPU or NPU work and belongs in a gang-scheduled group inside one scale-up
domain. The gateway in step 1 is what DeepInfer's README leaves as "load
balancing across data-parallel replicas."

## What stays AI Infra work

| DeepInfer / recipe gap | Why it is platform work | Where this repo covers it |
| --- | --- | --- |
| KV cache beyond one benchmark run | Prefix reuse across requests, nodes, and storage tiers | [Caching](./caching.md), Mooncake, LMCache |
| VE / prefill / decode as separately scaled roles | The engine can split the stages; the service has to place, order, and autoscale them | [P/D disaggregation](./pd-disaggregation.md), [Grove](./grove.md), [Dynamo](./dynamo.md), llm-d, LWS |
| DP load balancing for prefill and decode | Replica choice depends on cache locality and queue depth | Gateway API Inference Extension, AIBrix Gateway, Kthena Router |
| Tool execution | Recipe parses tool calls and stops there | Agent runtimes in [AI Gateway & Agentic Workflow](../../README.md#-3-ai-gateway--agentic-workflow) |
| HTTP, auth, multi-tenant isolation | Recipe and the offline engine do not terminate client traffic | Gateway projects, [isolation](../kubernetes/isolation.md) |
| Scale-up placement for EP/CP groups | Published curves use 4 and 64 SM100 GPUs, each in one scale-up domain | [SuperNode](../hardware/supernode.md), Grove topology placement, DRA |

Use DeepInfer when the workload is DeepSeek-V4.1-Flash and the goal is the
production kernel and parallelism path on SM100 or Ascend 950. Use
deepseek-recipe when an existing gateway or API server must speak DeepSeek V4
/ V4.1 prompts without reimplementing chat templates. Keep vLLM or SGLang
when the platform must serve many model families behind one orchestration
API; both already absorb DeepSeek kernels, and DeepInfer does not remove the
need for that platform.

## References

- [DeepInfer](https://github.com/deepseek-ai/DeepInfer)
- [deepseek-recipe](https://github.com/deepseek-ai/deepseek-recipe)
- [deepseek-recipe 0.2.0](https://docs.rs/crate/deepseek-recipe/latest)
- [DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)
- [Open-sourcing the DeepSeek inference engine (2025 direction note)](https://github.com/deepseek-ai/open-infra-index/blob/main/OpenSourcing_DeepSeek_Inference_Engine/README.md)
- [Day 6: DeepSeek-V3/R1 inference system overview](https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md)
