# Caching in LLM Inference

This document covers caching mechanisms in Large Language Model (LLM) inference,
focusing on prefix caching approaches that optimize performance by reusing
computed key-value (KV) cache across requests.

## Table of Contents

- [What is Prefix Caching](#what-is-prefix-caching)
- [Shared Prefix Caching](#shared-prefix-caching)
- [Independent Prefix Caching](#independent-prefix-caching)
- [Project Implementations](#project-implementations)
- [References](#references)

---

## What is Prefix Caching

Prefix caching in LLM inference optimizes performance by storing and reusing
previously computed key-value (KV) cache data. When multiple requests share
common prefixes (e.g., system prompts, chat history), the computation for
these shared portions can be cached and reused, significantly reducing
Time To First Token (TTFT) and improving throughput.

**Benefits:**

- Reduced computation for repeated prefixes
- Lower Time To First Token (TTFT)
- Higher overall throughput
- Better resource utilization
- Cost reduction in serving scenarios

---

## Shared Prefix Caching

Shared prefix caching allows multiple requests to share KV cache for common
prefixes across different sessions or users.

### NIXL

[`NIXL`](https://github.com/ai-dynamo/nixl) provides shared prefix caching
capabilities for LLM inference systems.

**Key Features:**

- Cross-request prefix sharing
- Integration with multiple inference engines
- Efficient cache management

### DCN (Distributed Compute Node)

DCN architecture enables distributed prefix caching across multiple compute
nodes. Originally from Red Hat OpenStack Platform, DCN provides:

- **Distributed compute node (DCN) architecture**: For edge use cases
  allowing remote compute and storage nodes to be deployed remotely while
  sharing a common centralized control plane
- **Strategic workload positioning**: Allows positioning workloads closer
  to operational needs for higher performance
- **Shared caching layer**: Enables prefix cache sharing across distributed
  nodes

For more details, see the [Red Hat DCN Documentation](https://docs.redhat.com/en/documentation/red_hat_openstack_platform/17.1/html/deploying_a_distributed_compute_node_dcn_architecture/understanding_dcn).

---

## Independent Prefix Caching

Independent prefix caching systems manage KV cache independently for each
session or service, providing isolation while still optimizing for repeated
patterns within individual contexts.

### LMCache

[`LMCache`](https://github.com/LMCache/lmcache) is an LLM serving engine
extension to reduce TTFT and increase throughput, especially under
long-context scenarios.

**Key Features:**

- Non-prefix KV cache support
- Integration with vLLM production stack, llm-d, and KServe
- Optimized for long-context scenarios
- Stable support for various cache patterns

### Dynamo KVBM

Dynamo's Key-Value Block Manager (KVBM) provides efficient KV cache
management within the Dynamo ecosystem.

**Key Features:**

- Block-based KV cache management
- Integration with Dynamo's disaggregated serving architecture
- Efficient memory utilization

For architecture details, see the
[KVBM Architecture Documentation](https://github.com/ai-dynamo/dynamo/blob/main/docs/architecture/kvbm_architecture.md).

### Host Memory Caching

Host memory caching utilizes system RAM for storing KV cache data,
providing:

- Lower cost compared to GPU memory
- Larger cache capacity
- Cross-GPU sharing capabilities
- Persistence across model reloads

---

## Project Implementations

### SGlang Storage Options

[`SGlang`](https://github.com/sgl-project/sglang) provides multiple storage
backends for KV cache management:

- **hf3fs deepseek HF3FS**: HuggingFace-based distributed file system
- **mooncake_store**: Mooncake as L3 KV Cache storage
- **nixl**: Integration with NIXL for shared prefix caching

Storage implementations can be found in the
[SGlang memory cache storage directory](https://github.com/sgl-project/sglang/tree/9b5f0f64f52033f5965d5b593df5df45c9be8c24/python/sglang/srt/mem_cache/storage).

### llm-d Routing Sidecar

The [`llm-d routing sidecar`](https://github.com/llm-d/llm-d-routing-sidecar)
supports multiple caching proxies:

- **NIXL integration**: Via NIXL v2 connector
- **LMCache support**: Direct integration with LMCache
- **Routing optimization**: Intelligent routing based on cache hit rates

Implementation details can be found in the
[NIXL v2 connector](https://github.com/llm-d/llm-d-routing-sidecar/blob/d84279a5eecfe098b7250df731576c69aa21505c/internal/proxy/connector_nixlv2.go).

---

## References

- [NIXL GitHub Repository](https://github.com/ai-dynamo/nixl)
- [LMCache GitHub Repository](https://github.com/LMCache/lmcache)
- [Dynamo KVBM Architecture](https://github.com/ai-dynamo/dynamo/blob/main/docs/architecture/kvbm_architecture.md)
- [SGlang Memory Cache Storage](https://github.com/sgl-project/sglang/tree/9b5f0f64f52033f5965d5b593df5df45c9be8c24/python/sglang/srt/mem_cache/storage)
- [llm-d Routing Sidecar](https://github.com/llm-d/llm-d-routing-sidecar)
- [Red Hat DCN Documentation](https://docs.redhat.com/en/documentation/red_hat_openstack_platform/17.1/html/deploying_a_distributed_compute_node_dcn_architecture/understanding_dcn)

**Some content was organized based on provided GitHub references. Please
verify technical details and current project status before implementation.**
