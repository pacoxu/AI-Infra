# Comparisons of LLM Inference Engines

Mainly compare AIBrix, llm-d, llmaz, OME and Kthena.

More details about specific platforms and techniques:

- [OME: Kubernetes Operator for LLM Management](./ome.md)
- [Caching in LLM Inference](./caching.md)
- [Memory, Context, and Database for AI Agents](./memory-context-db.md)
- [Large Scale Experts (MoE Models)](./large-scale-experts.md)
- [Model Lifecycle Management (Cold-Start, Sleep Mode, Offloading)](./model-lifecycle.md)

## Featured Projects

### AIBrix

[`AIBrix`](https://github.com/vllm-project/aibrix) is an open-source,
cloud-native solution optimized for deploying, managing, and scaling
large language model (LLM) inference in enterprise environments. As part
of the vLLM project ecosystem, AIBrix provides essential building blocks
for constructing scalable GenAI inference infrastructure.

**Key highlights:**

- High-density LoRA management and dynamic switching
- LLM-aware gateway and intelligent routing
- App-tailored autoscaling for LLM workloads
- Distributed inference and KV cache capabilities
- Cost-efficient heterogeneous serving with SLO guarantees

For detailed information, see [AIBrix Introduction](./aibrix.md).

### Kthena

[`Kthena`](https://github.com/volcano-sh/kthena) is a Kubernetes-native LLM
inference platform that transforms how organizations deploy and manage Large
Language Models in production. Kthena is part of the Volcano ecosystem and
provides comprehensive infrastructure for scalable LLM inference.

**Key highlights:**

- Kubernetes-native architecture for seamless cluster integration
- Production-ready LLM deployment and lifecycle management
- Optimized resource scheduling for inference workloads
- Enterprise-grade scalability and reliability

### llm-d

[`llm-d`](https://github.com/llm-d/llm-d) is a production-ready LLM inference
platform that implements Prefill-Decode disaggregation using a dual
LeaderWorkSet (LWS) architecture. llm-d demonstrates best practices for
orchestrating disaggregated inference workloads on Kubernetes.

**Key highlights:**

- Dual LWS architecture for P/D disaggregation
- LMCache integration for efficient KV cache management
- Routing sidecar for intelligent request routing
- Production-grade implementation for P/D disaggregation

For detailed information about P/D disaggregation implementations, see
[Prefill-Decode Disaggregation](./pd-disaggregation.md).

TODO:

- Add KServe detailed introduction (basic P/D disaggregation info added to
  [pd-disaggregation.md](./pd-disaggregation.md))
- Add llmaz detailed introduction
- Add comprehensive comparison table of inference engines (KServe, AIBrix,
  llmaz, OME, Kthena) to replace the previous reference tables

