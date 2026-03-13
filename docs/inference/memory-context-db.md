---
status: Active
maintainer: pacoxu
last_updated: 2025-10-29
tags: inference, memory, context, ai-agents, database
canonical_path: docs/inference/memory-context-db.md
---

# Memory, Context, and Database for AI Agents

This document covers memory management, context handling, and database
solutions for AI agents and LLM inference systems, focusing on both short-term
and long-term memory strategies.

## Table of Contents

- [Overview](#overview)
- [Short-Term vs Long-Term Memory](#short-term-vs-long-term-memory)
- [Agent Memory Architecture](#agent-memory-architecture)
- [Memory Backends](#memory-backends)
- [Vector Databases](#vector-databases)
- [State Management Solutions](#state-management-solutions)
- [Agent-Specific Database Systems](#agent-specific-database-systems)
- [Consistency and Garbage Collection](#consistency-and-garbage-collection)
- [Project Implementations](#project-implementations)
- [References](#references)

---

## Overview

Memory and context management are critical components for AI agents and LLM
applications. As agents become more sophisticated, they require efficient
mechanisms to store, retrieve, and manage both short-term conversational
context and long-term knowledge across sessions.

**Key Challenges:**

- Managing growing context windows and KV cache
- Balancing short-term chat history with long-term knowledge
- Ensuring consistency across thousands of concurrent agents
- Garbage collection for inactive agent sessions
- API standardization for memory operations

---

## Short-Term vs Long-Term Memory

### Short-Term Memory (Chat Context)

Short-term memory refers to the immediate conversational context within an
active session, typically stored in KV cache or working memory.

**Characteristics:**

- **Duration**: Active session only (seconds to hours)
- **Storage**: GPU VRAM, host RAM, or fast cache
- **Size**: Limited by context window (typically 4K-128K tokens)
- **Access Pattern**: Sequential, high-frequency reads/writes
- **Persistence**: Usually volatile, cleared after session ends

**Use Cases:**

- Multi-turn conversations
- In-session context tracking
- Immediate response generation
- Prompt caching for repeated prefixes

**Technologies:**

- KV Cache (see [Caching in LLM Inference](./caching.md))
- In-memory buffers
- Session-specific storage

### Long-Term Memory (Knowledge Base)

Long-term memory refers to persistent knowledge that survives across sessions,
enabling agents to recall past interactions and learned information.

**Characteristics:**

- **Duration**: Persistent across sessions (days to years)
- **Storage**: Databases, vector stores, object storage
- **Size**: Potentially unlimited (scaled by database capacity)
- **Access Pattern**: Random access, retrieval-based queries
- **Persistence**: Durable storage with backup and recovery

**Use Cases:**

- User preference tracking
- Historical conversation retrieval
- Domain-specific knowledge bases
- Personalization across sessions
- Multi-agent collaboration state

**Technologies:**

- Vector databases (Milvus, Chroma, Pinecone)
- Traditional databases (PostgreSQL, MySQL)
- Object stores (S3, GCS, MinIO)
- Graph databases for relationship tracking

---

## Agent Memory Architecture

Modern AI agents typically employ a hierarchical memory architecture that
combines multiple storage layers for optimal performance.

### Memory Hierarchy

```text
┌─────────────────────────────────────────────────────────┐
│                    Agent Application                     │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │Short-Term│    │ Working  │    │Long-Term │
   │ Memory   │    │ Memory   │    │ Memory   │
   └──────────┘    └──────────┘    └──────────┘
        │               │               │
   ┌────────┐    ┌──────────┐    ┌──────────┐
   │KV Cache│    │In-Memory │    │Vector DB │
   │ GPU/RAM│    │  State   │    │ Object   │
   └────────┘    └──────────┘    │  Store   │
                                  └──────────┘
```

### API Shapes for Agent Memory

According to CNCF TOC discussions, standardized API shapes are needed for:

- **State persistence**: Save and restore agent state
- **Memory retrieval**: Query historical interactions
- **Context injection**: Add external knowledge to prompts
- **Memory updates**: Incrementally update agent knowledge
- **Garbage collection**: Clean up inactive or expired memory

**Example API Operations:**

```text
GET    /agent/{id}/memory/recent       # Get recent conversation
POST   /agent/{id}/memory/store        # Store new memory
GET    /agent/{id}/memory/search       # Semantic search in memory
DELETE /agent/{id}/memory/prune        # Garbage collect old entries
GET    /agent/{id}/state               # Get full agent state
POST   /agent/{id}/state/restore       # Restore agent state
```

---

## Memory Backends

Different backend systems serve different memory management needs.

### Object Store (S3, GCS, MinIO)

**Best For**: Long-term storage of large context windows and conversation logs

**Characteristics:**

- Unlimited scalability
- Cost-effective for cold storage
- High durability and availability
- Slower access compared to databases

**Use Cases:**

- Archival of conversation history
- Checkpoint storage for long-running agents
- Backup and disaster recovery
- Compliance and audit logging

### Redis (In-Memory Cache)

**Best For**: Fast access to recent state and session data

**Characteristics:**

- Sub-millisecond latency
- Ephemeral or persistent storage modes
- Pub/sub for real-time updates
- TTL-based automatic expiration

**Use Cases:**

- Active session state
- Recent conversation history
- Distributed cache for agent state
- Rate limiting and request tracking

### Vector Databases

**Best For**: Semantic search and similarity-based retrieval

**Characteristics:**

- Embedding-based search
- Similarity scoring
- Metadata filtering
- Horizontal scalability

**Use Cases:**

- Semantic memory search
- RAG (Retrieval-Augmented Generation)
- Similar conversation retrieval
- Knowledge base queries

---

## Vector Database Implementations

Vector databases are essential for semantic search in agent memory systems.

### Key Projects

#### Chroma

[`Chroma`](https://github.com/chroma-core/chroma) is an open-source
embedding database designed for AI applications.

**Key Features:**

- Easy integration with LangChain and LlamaIndex
- Local or server deployment
- Python and JavaScript clients
- Metadata filtering and hybrid search

#### Milvus

<a href="https://github.com/milvus-io/milvus">`Milvus`</a> is a cloud-native
vector database built for scalable similarity search.

**Key Features:**

- CNCF Graduated Project
- Hybrid search (dense + sparse vectors)
- Multi-tenancy support
- Kubernetes-native deployment

#### Qdrant

<a href="https://github.com/qdrant/qdrant">`Qdrant`</a> is a vector similarity
search engine written in Rust, designed for high performance and production use.

**Key Features:**

- Built in Rust for high performance and reliability
- Payload filtering and hybrid search
- Distributed deployment support
- REST and gRPC APIs

#### Weaviate

<a href="https://github.com/weaviate/weaviate">`Weaviate`</a> is an open-source
vector database with built-in vectorizers and hybrid search.

**Key Features:**

- Built-in text and multi-modal vectorizers
- GraphQL and REST APIs
- Kubernetes-native deployment via operator

#### FAISS

<a href="https://github.com/facebookresearch/faiss">`FAISS`</a> (Facebook AI
Similarity Search) is a local indexing library for dense vector similarity
search.

**Key Features:**

- Highly optimized CPU/GPU similarity search
- Multiple index types (IVF, HNSW, PQ)
- Python and C++ interfaces
- Suitable for offline indexing and local embedding search

#### pgvector

<a href="https://github.com/pgvector/pgvector">`pgvector`</a> is a PostgreSQL
extension adding vector similarity search to Postgres.

**Key Features:**

- Native PostgreSQL integration
- Exact and approximate nearest-neighbor search (HNSW, IVFFlat)
- Combines vector search with relational queries
- Simple deployment for teams already using Postgres

### Kubernetes Operators

Vector database deployment on Kubernetes is simplified by dedicated operators:

- **Milvus Operator**: [Automates Milvus cluster management](https://github.com/milvus-io/milvus-operator)
- **Chroma Operator**: [Manages Chroma deployments](https://github.com/chroma-core/chroma-operator) (community-driven, repository is archived)
- **Weaviate Operator**: [Handles Weaviate vector database clusters](https://github.com/weaviate/weaviate-operator)

---

## State Management Solutions

### Dapr State Components

<a href="https://github.com/dapr/dapr">`Dapr`</a> (Distributed Application
Runtime) provides a unified state management API across multiple backends.

**Key Features:**

- Multi-backend support (Redis, PostgreSQL, CosmosDB, etc.)
- Consistent API across different stores
- Transaction support
- State encryption and concurrency control

**Benefits for Agent Systems:**

- Abstract away backend differences
- Easy backend switching for different environments
- Built-in retry and resilience patterns
- Service mesh integration

**Example State Stores:**

- Redis: Fast, ephemeral state
- PostgreSQL: Durable, transactional state
- CosmosDB: Globally distributed state
- Azure Blob Storage: Large object state

### Model Context Protocol (MCP)

Model Context Protocol aims to standardize how LLMs interact with external
context sources, including memory systems.

**Goals:**

- Standardized context injection
- Provider-agnostic memory access
- Efficient context retrieval
- Multi-modal context support

---

## Agent-Specific Database Systems

### memU

<a href="https://github.com/NevaMind-AI/memU">`memU`</a> is a memory
management solution specifically designed for AI agents.

**Key Features:**

- Persistent memory across agent sessions
- Hierarchical memory organization
- Efficient retrieval mechanisms
- Integration with popular agent frameworks

**Architecture:**

- Memory indexing for fast retrieval
- Vector similarity for semantic search
- Metadata tagging for context filtering
- Automatic memory consolidation

### DB-GPT

<a href="https://github.com/eosphoros-ai/DB-GPT">`DB-GPT`</a> is an
experimental AI-native database framework with built-in support for agent
memory.

**Key Features:**

- AI-native data management
- Natural language query interface
- Agent memory primitives
- Knowledge graph integration

**Use Cases:**

- Multi-agent systems with shared knowledge
- Complex reasoning over structured data
- Database-backed conversational agents
- Enterprise knowledge management

---

## Consistency and Garbage Collection

Managing state consistency and memory cleanup across thousands of concurrent
agents presents unique challenges.

### Consistency Challenges

**Problem Areas:**

- **Multi-agent coordination**: Agents reading/writing shared state
- **Distributed deployments**: State spread across multiple nodes
- **Session handoff**: Transferring agent state between replicas
- **Concurrent updates**: Multiple requests modifying same agent state

**Solutions:**

- **Optimistic locking**: Version-based conflict detection
- **Event sourcing**: Append-only state changes
- **CQRS**: Separate read/write models for scalability
- **Distributed transactions**: Two-phase commit for critical operations

### Garbage Collection Strategies

Automatic cleanup of inactive or expired agent memory is essential for system
health.

**TTL-Based Expiration:**

- Set time-to-live on memory entries
- Automatic deletion after expiration
- Redis native support for TTL
- Suitable for session-based state

**Reference Counting:**

- Track active references to agent state
- Delete when reference count reaches zero
- Useful for shared memory across agents

**LRU/LFU Eviction:**

- Least Recently Used or Least Frequently Used
- Keep hot data in cache, evict cold data
- Memory-bounded caches

**Manual Cleanup:**

- Explicit agent session termination
- User-initiated data deletion
- Compliance-driven data retention policies

**Background Jobs:**

- Periodic scan for inactive sessions
- Batch deletion of old entries
- Off-peak execution to minimize impact

---

## Project Implementations

### llm-d with LMCache

<a href="https://llm-d.ai/blog/kvcache-wins-you-can-see">`KV-Cache Wins You
Can See: From Prefix Caching in vLLM to Distributed Scheduling with
llm-d`</a> demonstrates practical KV cache management.

**Key Insights:**

- Prefix caching dramatically reduces TTFT
- Distributed scheduling enables efficient cache utilization
- Production deployment strategies for disaggregated inference
- Integration with LMCache for cross-node cache sharing

**Implementation Details:**

- LMCache integration for persistent KV cache
- Routing sidecar for intelligent request distribution
- Cache-aware scheduling for maximizing hit rates
- Monitoring and observability for cache performance

For more details on LMCache integration, see:

- [LMCache on GKE](https://blog.lmcache.ai/2025-10-07-LMCache-on-GKE/)
- [Dynamo LMCache Integration](https://blog.lmcache.ai/2025-09-18-dynamo-lmcache/)

### CNCF TOC Discussion on Agent Memory

The CNCF Technical Oversight Committee is discussing agent memory
requirements in
<a href="https://github.com/cncf/toc/issues/1746">TOC Issue #1746</a>.

**Key Topics:**

- **State & Memory Backends**: Which back-ends (object store, vector DB,
  Redis) and API shapes are suitable for short-term and long-term agent memory
- **Consistency**: How to ensure consistency across thousands of agents
- **Garbage Collection**: Strategies for cleaning up inactive agent state
- **Gap Identification**: Missing pieces in the current ecosystem, such as:
  - Standardized agent memory APIs
  - MCP-Kubernetes discovery mechanisms
  - Integration patterns for state management

**Proposed Solutions:**

- Dapr state components for backend abstraction
- Vector database operators (Chroma, Milvus) for semantic search
- S3/GCS for long-term storage
- Redis for hot state and caching

---

## References

### Projects

- [memU (NevaMind-AI)](https://github.com/NevaMind-AI/memU)
- [DB-GPT (eosphoros-ai)](https://github.com/eosphoros-ai/DB-GPT)
- [NIXL (ai-dynamo)](https://github.com/ai-dynamo/nixl)
- [LMCache](https://github.com/LMCache/lmcache)
- [Chroma](https://github.com/chroma-core/chroma)
- [Milvus](https://github.com/milvus-io/milvus)
- [Dapr](https://github.com/dapr/dapr)

### Blog Posts and Articles

- [KV-Cache Wins You Can See (llm-d)](https://llm-d.ai/blog/kvcache-wins-you-can-see)
- [LMCache on GKE](https://blog.lmcache.ai/2025-10-07-LMCache-on-GKE/)
- [Dynamo LMCache Integration](https://blog.lmcache.ai/2025-09-18-dynamo-lmcache/)

### Community Discussions

- [CNCF TOC Issue #1746: Agent Memory and State Management](https://github.com/cncf/toc/issues/1746)

### Related Documentation

- [Caching in LLM Inference](./caching.md) - KV cache and prefix caching
- [Prefill-Decode Disaggregation](./pd-disaggregation.md) - Distributed
  inference architecture
- [Model Lifecycle Management](./model-lifecycle.md) - Cold-start, sleep mode,
  and offloading

---

**Note**: This documentation consolidates information from multiple sources
including GitHub repositories, blog posts, and community discussions. Some
technologies and APIs are under active development. Please verify current
project status and capabilities before production implementation.
