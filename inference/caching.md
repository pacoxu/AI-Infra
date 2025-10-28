# Caching in LLM Inference

This document covers caching mechanisms in Large Language Model (LLM) inference,
focusing on prefix caching approaches that optimize performance by reusing
computed key-value (KV) cache across requests.

## Table of Contents

- [What is Prefix Caching](#what-is-prefix-caching)
- [KV Cache Offloading and Storage Hierarchy](#kv-cache-offloading-and-storage-hierarchy)
- [Shared Prefix Caching](#shared-prefix-caching)
- [Independent Prefix Caching](#independent-prefix-caching)
- [Distributed KV Cache Solutions](#distributed-kv-cache-solutions)
- [Network Acceleration for KV Cache Transfer](#network-acceleration-for-kv-cache-transfer)
- [Next-Generation Hardware for KV Cache](#next-generation-hardware-for-kv-cache)
- [KV Cache Solutions Comparison](#kv-cache-solutions-comparison)
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

## KV Cache Offloading and Storage Hierarchy

As LLM context windows continue to expand, KV cache storage requirements grow
exponentially. To manage this growth, modern inference systems employ a
hierarchical storage approach, offloading KV cache data across multiple
storage tiers based on access patterns and performance requirements.

### Storage Hierarchy

The KV cache storage hierarchy typically follows this pattern, ordered by
access speed and cost:

1. **VRAM (GPU Memory)**: Fastest access, highest cost, limited capacity
   - Primary storage for active KV cache during inference
   - Lowest latency for attention computation
   - Typical capacity: 16GB - 80GB per GPU

2. **RAM (Host Memory)**: Fast access, moderate cost, larger capacity
   - Intermediate storage for warm KV cache
   - Shared across multiple GPUs on the same node
   - Typical capacity: 256GB - 2TB per node

3. **SSD (Solid State Drive)**: Moderate access speed, lower cost
   - Storage for cold KV cache with high-speed access requirements
   - Persistent across system restarts
   - Typical capacity: 1TB - 16TB per node

4. **Local Disk (HDD)**: Slower access, low cost, high capacity
   - Archival storage for infrequently accessed KV cache
   - Long-term persistence
   - Typical capacity: 4TB - 100TB per node

5. **Remote Object Storage**: Network-based, lowest cost, unlimited scale
   - Distributed storage for shared KV cache across clusters
   - Enables cross-node KV cache sharing
   - Examples: S3, OSS, Ceph, MinIO

### Offloading Strategies

Effective KV cache offloading requires intelligent management:

- **Automatic tiering**: Move KV cache between tiers based on access patterns
- **Prefetching**: Load KV cache from slower tiers before needed
- **Compression**: Reduce storage requirements and transfer bandwidth
- **Deduplication**: Share identical KV cache blocks across requests
- **Eviction policies**: LRU, LFU, or application-aware eviction strategies

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

> **Note**: The DCN (Distributed Compute Node) architecture referenced here
> is primarily an OpenStack cloud infrastructure concept. While the distributed
> caching principles may apply to LLM inference scenarios, this documentation
> link refers to general edge computing deployment patterns rather than
> LLM-specific caching implementations. Further research is needed to validate
> specific DCN applications for LLM inference prefix caching.

---

## Distributed KV Cache Solutions

Distributed KV cache systems manage KV cache across multiple nodes, enabling
efficient sharing and offloading to remote storage. These solutions are
critical for scaling LLM inference to handle large context windows and
high-throughput serving scenarios.

### Mooncake

[`Mooncake`](https://github.com/kvcache-ai/Mooncake) is a distributed KV cache
service designed to alleviate storage pressure in LLM inference systems. It
addresses the exponential growth in KV cache storage requirements as model
context windows expand.

**Key Features:**

- **Distributed KV Cache Management**: Shares KV cache across multiple nodes
- **L3 KV Cache Storage**: Provides an additional caching layer beyond GPU
  and host memory
- **High-throughput Transfer**: Optimized for cross-node data movement
- **Integration with Inference Engines**: Works with SGlang and other
  inference frameworks
- **Persistent Storage**: Enables KV cache persistence across service restarts

**Architecture:**

Mooncake implements a distributed architecture that separates cache storage
from compute nodes:

- **Cache Storage Nodes**: Dedicated nodes for storing KV cache data
- **Compute Nodes**: Inference nodes that generate and consume KV cache
- **Metadata Management**: Tracks KV cache location and access patterns
- **Transfer Optimization**: Minimizes cross-node data transfer overhead

**Performance Considerations:**

While Mooncake and similar distributed KV cache services reduce storage
pressure, cross-node data transfer remains a primary performance bottleneck.
Network latency and bandwidth limitations can impact overall system throughput,
especially for long-context scenarios.

### Next-Generation Hardware Integration

Modern distributed KV cache solutions increasingly leverage next-generation
hardware capabilities to overcome network bottlenecks:

- **Ultra-high Bandwidth (UB) Interconnects**: 400Gbps+ bandwidth for
  high-speed cross-node communication
- **CXL (Compute Express Link)**: Memory-semantic access to remote memory
  with low latency
- **Lingqiao SuperNode Shared Memory**: Hardware-accelerated shared memory
  across nodes

These hardware advancements are highly compatible with distributed KV cache
management requirements, providing:

- High bandwidth for large KV cache transfers
- Low latency for real-time inference workloads
- Memory-semantic access patterns matching KV cache usage
- Unified memory view across distributed nodes

**Industry Initiatives:**

The Chinese AI infrastructure community is actively developing solutions that
integrate next-generation hardware with distributed KV cache services. For
example, proposals exist to integrate Lingqiao SuperNode shared memory
capabilities into Mooncake, leveraging next-generation hardware features to
provide universal acceleration for inference services.

### Other Distributed KV Cache Solutions

Several other projects provide distributed KV cache capabilities:

- **AIBrix**: Includes distributed inference and KV cache capabilities within
  the vLLM ecosystem
- **Vineyard**: Used by AIBrix for distributed KV cache management
- **Ray Distributed Runtime**: Provides distributed memory management for
  multi-node inference

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

## Network Acceleration for KV Cache Transfer

As distributed KV cache systems move data across nodes, network performance
becomes critical. Modern inference systems leverage high-performance
networking technologies to minimize transfer latency and maximize throughput.

### RDMA (Remote Direct Memory Access)

RDMA enables direct memory access from one computer to another without
involving either operating system, reducing latency and CPU overhead.

**Benefits for KV Cache Transfer:**

- **Zero-copy transfers**: Direct memory-to-memory copy without CPU involvement
- **Kernel bypass**: Eliminates operating system overhead
- **Low latency**: Sub-microsecond latency for memory access
- **High bandwidth**: 100Gbps to 400Gbps+ throughput
- **CPU offload**: Frees CPU resources for inference computation

**RDMA Technologies:**

- **InfiniBand**: Purpose-built for high-performance computing
  - Lowest latency and highest bandwidth
  - Common in AI/ML clusters and datacenters
  - Typical bandwidth: 200Gbps (HDR), 400Gbps (NDR), 800Gbps (XDR, emerging)

- **RoCE (RDMA over Converged Ethernet)**: RDMA over Ethernet networks
  - More cost-effective than InfiniBand
  - Leverages existing Ethernet infrastructure
  - Typical bandwidth: 100Gbps, 200Gbps, 400Gbps

- **iWARP**: Internet Wide Area RDMA Protocol
  - Works over standard TCP/IP networks
  - Better for WAN scenarios

**Implementation Considerations:**

For effective RDMA-based KV cache transfer:

- Use verbs API for direct RDMA operations
- Implement connection pooling for multiple inference requests
- Consider memory registration overhead for frequently accessed cache
- Optimize buffer management to minimize copying
- Monitor network congestion and adjust transfer patterns

### InfiniBand for LLM Inference

InfiniBand is particularly well-suited for distributed LLM inference due to:

- **Low latency**: Critical for real-time inference with tight SLO requirements
- **High bandwidth**: Supports large KV cache transfers for long contexts
- **Native RDMA support**: Hardware-optimized for direct memory access
- **Scalability**: Supports large-scale clusters with thousands of nodes
- **Reliability**: Built-in error detection and recovery mechanisms

**Typical Deployment:**

In production LLM serving clusters:

- InfiniBand connects GPU nodes within a datacenter
- Enables efficient KV cache sharing across distributed inference workers
- Supports disaggregated prefill-decode architectures
- Facilitates model parallelism and tensor parallelism

---

## Next-Generation Hardware for KV Cache

Beyond traditional RDMA and InfiniBand, emerging hardware technologies are
transforming distributed KV cache management with memory-semantic access
and ultra-high bandwidth.

### CXL (Compute Express Link)

CXL is an open standard interconnect that enables high-speed, efficient
communication between CPUs, memory, accelerators, and other devices.

**Key Capabilities for KV Cache:**

- **Memory pooling**: Shared memory pools across multiple hosts
- **Cache coherency**: Hardware-managed coherent memory access
- **Low latency**: Near-memory access speeds for remote memory
- **Bandwidth**: 64-256 GB/s per link (CXL 2.0/3.0)
- **Memory expansion**: Dynamically expand available memory capacity

**Benefits for Distributed KV Cache:**

- Treat remote KV cache as local memory with minimal latency
- Hardware-managed coherency eliminates software overhead
- Flexible memory allocation across distributed nodes
- Cost-effective memory expansion without full system upgrades

### Ultra-High Bandwidth (UB) Interconnects

Next-generation interconnects provide unprecedented bandwidth for data
movement:

- **400GbE and beyond**: Next-generation Ethernet at 400Gbps, 800Gbps
- **800G InfiniBand (XDR)**: Emerging InfiniBand standard
- **Custom AI interconnects**: Vendor-specific high-bandwidth solutions

**Impact on KV Cache Performance:**

Higher bandwidth interconnects enable:

- Faster KV cache transfers for long-context scenarios
- Reduced transfer time as a percentage of total inference time
- Support for larger batch sizes with distributed cache
- Efficient prefetching and background cache movement

### Lingqiao SuperNode Shared Memory

Lingqiao SuperNode technology provides hardware-accelerated shared memory
across physically distributed nodes, creating a unified memory space.

**Key Features:**

- **Memory-semantic access**: Access remote memory as if it were local
- **Hardware acceleration**: Dedicated hardware for memory virtualization
- **Low latency**: Optimized for real-time inference requirements
- **High bandwidth**: Supports large-scale KV cache transfers

**Integration with Distributed KV Cache:**

Proposals exist to integrate Lingqiao SuperNode capabilities with services
like Mooncake, enabling:

- Seamless KV cache sharing across nodes without explicit data transfer
- Reduced software complexity for distributed cache management
- Hardware-optimized performance for inference acceleration
- Universal solution for next-generation inference infrastructure

---

## KV Cache Solutions Comparison

The following table compares the three major KV cache solutions: NIXL,
LMCache, and Mooncake.

<!-- markdownlint-disable MD013 -->
| Feature | NIXL | LMCache | Mooncake |
|---------|------|---------|----------|
| **Project Type** | Shared prefix caching | Independent prefix caching | Distributed KV cache service |
| **Primary Use Case** | Cross-request prefix sharing | Long-context TTFT reduction | Distributed storage management |
| **Caching Scope** | Shared across requests/users | Per-session/service | Cluster-wide distributed |
| **Integration** | Multiple inference engines | vLLM, llm-d, KServe | SGlang, inference frameworks |
| **Storage Layer** | L2 cache (prefix sharing) | L2 cache (session cache) | L3 cache (distributed storage) |
| **Distribution** | Single/multi-node | Single/multi-node | Multi-node distributed |
| **Context Window** | Short to medium | Long-context optimized | Very long contexts |
| **RDMA Support** | Possible | Possible | Designed for high-speed network |
| **Hardware Acceleration** | Standard | Standard | Next-gen hardware ready (CXL, UB) |
| **Persistence** | In-memory | Configurable | Persistent distributed storage |
| **Best For** | Common prefix scenarios | Long-context inference | Large-scale distributed inference |
| **Maturity** | Production-ready | Production-ready | Active development |
<!-- markdownlint-enable MD013 -->

**Choosing the Right Solution:**

- **Use NIXL when**: You have many requests sharing common prefixes (e.g.,
  system prompts, common context)
- **Use LMCache when**: You need to optimize TTFT for long-context scenarios
  with stable integration in vLLM production stacks
- **Use Mooncake when**: You need distributed KV cache management across
  multiple nodes for extreme scale
- **Use combinations**: Many production systems combine multiple approaches
  (e.g., LMCache for local caching + Mooncake for distributed storage)

---

## Project Implementations

### SGlang Storage Options

[`SGlang`](https://github.com/sgl-project/sglang) provides multiple storage
backends for KV cache management:

- **hf3fs deepseek HF3FS**: HuggingFace-based distributed file system
- **mooncake_store**: Mooncake integration for L3 KV Cache distributed storage
  - Enables cross-node KV cache sharing
  - Supports persistent storage across service restarts
  - Optimized for large-scale inference deployments
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
- [Mooncake GitHub Repository](https://github.com/kvcache-ai/Mooncake)
- [Dynamo KVBM Architecture](https://github.com/ai-dynamo/dynamo/blob/main/docs/architecture/kvbm_architecture.md)
- [SGlang Memory Cache Storage](https://github.com/sgl-project/sglang/tree/9b5f0f64f52033f5965d5b593df5df45c9be8c24/python/sglang/srt/mem_cache/storage)
- [llm-d Routing Sidecar](https://github.com/llm-d/llm-d-routing-sidecar)
- [Red Hat DCN Documentation](https://docs.redhat.com/en/documentation/red_hat_openstack_platform/17.1/html/deploying_a_distributed_compute_node_dcn_architecture/understanding_dcn)
- [InfiniBand Trade Association](https://www.infinibandta.org/)
- [CXL Consortium](https://www.computeexpresslink.org/)
- [RDMA Programming Guide](https://www.rdmamojo.com/)

**Some content was organized based on provided GitHub references. Please
verify technical details and current project status before implementation.**
