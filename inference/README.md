# Comparisons of LLM Inference Engines

Mainly compare AIBrix, llm-d, llmaz and OME.

More details about specific platforms:

- [OME: Kubernetes Operator for LLM Management](./ome.md)

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


TODO:

- Add llm-d
- Add KServe detailed introduction
- Add llmaz detailed introduction

I will add a new table to compare the features of the inference engines.
Hence, I will remove the below previous references tables.

## Previous References

1. [KServe, AIBrix and llmaz (March, 2025)](https://docs.google.com/presentation/d/1jzfi6iWnAg3Cz0PGEJhZrvRls4dcGBENiY529huoyys/edit?usp=sharing) by llmaz owner.

| Feature                        | KServe                                   | AIBrix                                               | llmaz                                         |
|-------------------------------|------------------------------------------|------------------------------------------------------|-----------------------------------------------|
| Name                          | KServe                                   | AIBrix                                               | llmaz                                         |
| Easy of Use                   | Medium                                   | Hard                                                 | Easy                                          |
| Inference Engine (In-Tree)    | HF, vLLM                                 | vLLM                                                 | vLLM, SGLang, llama.cpp, TGI, Ollama          |
| Model Cache                   | Limited (node share)                     | No                                                   | Limited (with Manta, reframing now)          |
| Model Load Accelerator        | No                                       | Yes (with GPU Streaming)                             | No                                            |
| Scale-to-Zero                 | Yes (Knative)                            | No                                                   | No                                            |
| Multi-Host                    | Yes (with multiple deployments)          | Yes (with ray cluster)                               | Yes (with LWS)                                |
| Multi-LoRA                    | No                                       | Yes (dynamic LoRA switching)                         | No (WIP with LoRA autoscaling)               |
| LoRA Aware Routing            | No (WIP with Envoy AI Gateway)           | Yes                                                  | No (WIP with LoRA autoscaling)               |
| Prefix Cache Aware            | No (WIP with Envoy AI Gateway)           | Yes                                                  | No                                            |
| PD disaggregated Serving      | No                                       | No                                                   | Limited (with LWS)                            |
| Heterogeneous Accelerators    | No                                       | Yes                                                  | Yes (with scheduler plugins installed)        |
| GPU Failure Detector          | No                                       | Yes                                                  | No                                            |
| Pod Autoscaling               | HPA                                      | HPA, KPA, APA (llm optimized)                        | HPA                                           |
| Distributed KV Cache          | No                                       | Yes (with Vineyard and internal vLLM)                | No                                            |

2. Simple Comparison of LLM Inference Engines (May, 2025) by [XiaoQing](https://x.com/xiaoqing224486/status/1896148173183410281) on X.com.

| Feature         | KubeAI             | BentoML                          | KServe            | AIBrix              | Llama Stack           | Ilmaz              | KubeRay                  | MLflow                  | SkyPilot                   | Kaito                  |
|----------------|--------------------|----------------------------------|-------------------|----------------------|------------------------|---------------------|---------------------------|--------------------------|----------------------------|------------------------|
| Supported Model| LLM, Multi-modal   | Any ML model                     | General ML model  | LLM (vLLM)           | LLaMA and other LLMs   | LLM                 | Any Ray model             | Any ML model             | Any AI/ML task             | Open-source LLM        |
| API            | OpenAI Compatible  | Custom REST                      | REST/gRPC         | OpenAI + Custom      | OpenAI + Standard      | OpenAI Compatible   | REST + Ray API            | REST                     | No direct API              | OpenAI Compatible      |
| Main Feature   | Inference Optim    | Packaging & Deployment           | Inference Service | Large-scale Inference| App Development        | Prod Inference      | Distributed Task Mgmt     | Experiment Mgmt & Deploy| Cloud Task Scheduling      | Inference + GPU Mgmt   |
| Scalability    | Scale-from-Zero    | Manual or External Tool, BentoCloud supports both | Scale-to-Zero     | Dynamic Scaling       | Reliable Backend       | HPA + Smart Scaling | Ray + K8s Scaling         | Medium                    | Cross-cloud Distributed    | Auto GPU Scaling       |
| Deployment Env | Kubernetes         | Any (Local, Docker, BentoCloud, K8s) | Kubernetes    | Kubernetes           | Local/Container/Cloud  | Kubernetes          | Kubernetes                | Any                      | Multi-cloud/Local/K8s      | Kubernetes (AKS)       |
| Extra Feature  | Model Cache        | Version Control                  | Pre-processing    | Gateway Routing      | Memory, Tools          | Multi-backend Support| RayJob                    | Experiment Tracking       | Cost Optimization          | Auto Node Placement    |
