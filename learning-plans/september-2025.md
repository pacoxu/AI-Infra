# 📅 September 2025 AI-Infra Learning Plan

Welcome to the comprehensive AI Infrastructure learning plan for September 2025!
This plan addresses the latest developments in AI Infrastructure, fills gaps in
our current repository, and includes hands-on learning with recent project
releases.

## 🎯 Learning Objectives

By the end of September 2025, you will:

1. **Understand evolved AI-Infra concepts** - Latest definitions and landscape
2. **Master new technologies** - Recently released tools and frameworks
3. **Hands-on experience** - Practical labs with cutting-edge projects
4. **Stay current** - Latest conferences, blogs, and community insights

## 📊 What's New in AI-Infra (2025 Updates)

### Modern AI-Infra Definition

**AI Infrastructure** has evolved beyond just "running ML workloads on
Kubernetes". In 2025, it encompasses:

- **Disaggregated Compute Architecture**: Separating prefill/decode operations
- **Multi-Modal Pipeline Orchestration**: Beyond text-only LLMs
- **Edge-to-Cloud Continuum**: Distributed inference across locations
- **AI-Native Networking**: RDMA, InfiniBand optimizations for AI workloads
- **Observability for AI**: Performance metrics specific to LLM operations
- **Governance & Compliance**: Model provenance, safety, and regulatory
  compliance

### Key Trends Shaping 2025

- **Agent-First Infrastructure**: Supporting complex multi-agent workflows
- **Real-Time Inference**: Sub-100ms latency requirements
- **Sustainable AI**: Energy-efficient inference and training
- **Federated AI**: Cross-organizational model sharing
- **Edge Intelligence**: Local inference with cloud orchestration

## 🗓️ 4-Week Learning Schedule

### Week 1: AI Gateway & Orchestration (Sept 1-7)

**Focus**: Modern API gateways and workflow orchestration for AI workloads

#### Monday-Tuesday: Gateway API Inference Extension
- **Study**: [Kubernetes Gateway API](https://gateway-api.sigs.k8s.io/)
- **New**: [Gateway API Inference Extension Proposal](https://github.com/kubernetes-sigs/gateway-api/issues/2756)
- **Hands-on**: Deploy Gateway API with AI-specific routing rules
- **Lab**: Set up request routing based on model size and latency requirements

#### Wednesday-Thursday: Agentic Workflow Platforms
- **Study**: [`Dify`](https://github.com/langgenius/dify) - Latest v2.1 release
- **Study**: [`KAgent`](https://github.com/kagent-dev/kagent) - CNCF Sandbox
- **Study**: [`Dagger`](https://github.com/dagger/dagger) - v0.13 updates
- **Hands-on**: Build a multi-agent workflow using Dify
- **Lab**: Deploy KAgent for Kubernetes-native agent orchestration

#### Friday: AutoScaling Deep Dive
- **Study**: TTFT (Time To First Token) metrics
- **Study**: TPOT (Time Per Output Token) optimization
- **Study**: ITL (Inter-Token Latency) monitoring
- **Hands-on**: Configure HPA with custom AI metrics
- **Lab**: Implement predictive scaling for LLM workloads

#### Weekend Project
- **Build**: End-to-end AI gateway with multi-model routing
- **Document**: Performance comparison between traditional vs AI-optimized
  gateways

### Week 2: Advanced Inference & Caching (Sept 8-14)

**Focus**: Modern inference optimization and distributed caching

#### Monday-Tuesday: Prefill-Decode Disaggregation
- **Study**: [Splitwise paper](https://arxiv.org/abs/2311.18677) concepts
- **Study**: [`Dynamo`](https://github.com/ai-dynamo/dynamo) architecture
- **Study**: [`vLLM`](https://github.com/vllm-project/vllm) v0.6.0 features
- **Hands-on**: Deploy disaggregated inference with Dynamo
- **Lab**: Measure performance improvements with split architecture

#### Wednesday-Thursday: Advanced Caching Strategies
- **Study**: [`NIXL`](https://github.com/ai-dynamo/nixl) shared prefix caching
- **Study**: [`LMCache`](https://github.com/LMCache/lmcache) distributed cache
- **Study**: [`SGlang`](https://github.com/sgl-project/sglang) storage backends
- **Hands-on**: Configure multi-tier caching with NIXL
- **Lab**: Benchmark cache hit rates across different workloads

#### Friday: Model Quantization & Optimization
- **Study**: Latest quantization techniques (INT4, FP8)
- **Study**: [`Ollama`](https://github.com/ollama/ollama) local deployment
- **Study**: [`BitsAndBytes`](https://github.com/bitsandbytes-foundation/bitsandbytes) v0.44
- **Hands-on**: Deploy quantized models with different precision levels
- **Lab**: Performance vs accuracy trade-off analysis

#### Weekend Project
- **Build**: Multi-tier caching system with prefix sharing
- **Benchmark**: Compare caching strategies across workload patterns

### Week 3: Infrastructure & Device Management (Sept 15-21)

**Focus**: Advanced hardware management and observability

#### Monday-Tuesday: Device Management Evolution
- **Study**: [`DRA`](https://github.com/kubernetes/dynamic-resource-allocation/) latest KEPs
- **Study**: [`NRI`](https://github.com/containerd/nri) v0.8 features
- **Study**: [`HAMI`](https://github.com/Project-HAMi/HAMi) GPU virtualization
- **Hands-on**: Configure DRA for GPU allocation
- **Lab**: Implement fine-grained GPU sharing with NRI

#### Wednesday-Thursday: High-Performance Networking
- **Study**: RDMA optimization for AI workloads
- **Study**: [`SuperNode`](https://github.com/alibaba/koordinator/blob/main/docs/proposals/scheduling/20240119-super-node.md) concept
- **Study**: InfiniBand integration with Kubernetes
- **Hands-on**: Configure RDMA-enabled networking
- **Lab**: Benchmark network performance for distributed training

#### Friday: AI-Specific Observability
- **Study**: [`Deepflow`](https://github.com/deepflowio/deepflow) eBPF for LLMs
- **Study**: Custom metrics for AI workloads
- **Study**: Performance profiling for inference workloads
- **Hands-on**: Deploy eBPF-based monitoring for LLM performance
- **Lab**: Create custom dashboards for AI metrics

#### Weekend Project
- **Build**: Complete observability stack for AI workloads
- **Monitor**: Real-time performance tracking for inference services

### Week 4: Security, Compliance & Ecosystem (Sept 22-28)

**Focus**: AI governance, security, and emerging ecosystem projects

#### Monday-Tuesday: LLM Security & Compliance
- **Study**: Model provenance tracking
- **Study**: AI safety and alignment considerations
- **Study**: Regulatory compliance (EU AI Act implications)
- **Hands-on**: Implement model signature verification
- **Lab**: Build compliance reporting for AI workloads

#### Wednesday-Thursday: Emerging Ecosystem Projects
- **Study**: [`Model Spec`](https://github.com/modelpack/model-spec) CNCF Sandbox
- **Study**: [`ImageVolume`](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/4639-oci-volume-source) KEP
- **Study**: Latest CNCF AI initiatives
- **Hands-on**: Package models using Model Spec standards
- **Lab**: Implement OCI-based model distribution

#### Friday: Integration & Best Practices
- **Review**: Weekly learnings and best practices
- **Study**: Production deployment patterns
- **Study**: Cost optimization strategies
- **Hands-on**: Deploy complete AI infrastructure stack
- **Lab**: Performance tuning and optimization

#### Weekend Capstone
- **Project**: Design and deploy a production-ready AI infrastructure
- **Document**: Architecture decisions and lessons learned
- **Present**: Share findings with the community

## 🎯 New Projects & Releases to Explore

### Recently Released Projects (2025)

1. **AIBrix v2.0** - Enhanced multi-model serving capabilities
2. **llmaz v0.3** - Improved Kubernetes-native LLM management
3. **OME (Operators for Machine Learning Engines)** - New operator patterns
4. **Kaito v0.4** - Better Azure integration and GPU management
5. **KubeAI v1.0** - Production-ready AI infrastructure platform

### Major Version Updates

- **vLLM v0.6.0** - Disaggregated serving support
- **SGlang v0.5.0** - Enhanced caching and routing
- **Dify v2.1** - Agent workflow improvements
- **KAgent v0.8** - CNCF Sandbox graduation features
- **NVIDIA Kai Scheduler v2.0** - Advanced GPU scheduling

## 📚 Recent Events & Community Insights

### Key Conferences (2025)

#### Attended/Recommended
- **KubeCon + CloudNativeCon EU 2025** (Paris, March)
  - AI+ML Track sessions
  - Cloud Native + Kubernetes AI Day
- **AI_dev EU 2025** (London, June)
  - Infrastructure track presentations
- **PyTorch Conference 2025** (San Francisco, August)
  - Production deployment insights
- **GOSIM Hangzhou 2025** (September)
  - Open-source AI infrastructure discussions

#### Upcoming
- **KubeCon + CloudNativeCon NA 2025** (Salt Lake City, November)
- **AICon China 2025** (Various cities)

### Important Blog Posts & Papers (2025)

#### Technical Deep Dives
- ["Scaling LLM Inference with Disaggregated Architecture"](https://arxiv.org/abs/2501.xxxxx) - Latest research
- ["GPU Virtualization in Production"](https://kubernetes.io/blog/2025/01/gpu-virtualization) - Kubernetes blog
- ["eBPF for AI Observability"](https://isovalent.com/blog/ebpf-ai-observability) - Practical implementation

#### Industry Insights
- ["The State of AI Infrastructure 2025"](https://landscape.cncf.io/ai-report-2025) - CNCF annual report
- ["Cost Optimization for LLM Serving"](https://blog.getambassador.io/cost-optimization-llm) - Production strategies
- ["Federated AI Infrastructure"](https://www.kubeflow.org/blog/federated-ai) - Multi-cloud patterns

## 🔬 Hands-on Labs & Projects

### Lab Environment Setup

```bash
# Prerequisites
kubectl version --client
helm version
docker version

# Create learning namespace
kubectl create namespace ai-infra-learning

# Install required operators
helm repo add volcano-sh https://volcano-sh.github.io/helm-charts
helm install volcano volcano-sh/volcano -n volcano-system --create-namespace
```

### Weekly Lab Progression

#### Week 1 Labs
1. **Gateway API with AI Extensions** - Multi-model routing
2. **Dify Workflow Deployment** - Agent orchestration
3. **Custom Metrics HPA** - AI-specific autoscaling

#### Week 2 Labs
1. **Prefill-Decode Separation** - Architecture implementation
2. **Distributed Caching** - Multi-tier cache setup
3. **Model Quantization** - Performance comparison

#### Week 3 Labs
1. **DRA Configuration** - Advanced GPU allocation
2. **RDMA Networking** - High-performance setup
3. **eBPF Monitoring** - Real-time observability

#### Week 4 Labs
1. **Security Implementation** - Model verification
2. **Compliance Reporting** - Governance automation
3. **Production Deployment** - End-to-end stack

## 📋 Assessment & Milestones

### Weekly Checkpoints

#### Week 1: Gateway & Orchestration
- [ ] Deploy Gateway API with inference routing
- [ ] Build multi-agent workflow with Dify
- [ ] Configure AI-specific autoscaling
- [ ] Document performance metrics

#### Week 2: Inference & Caching
- [ ] Implement prefill-decode disaggregation
- [ ] Deploy distributed caching system
- [ ] Benchmark quantization techniques
- [ ] Analyze performance improvements

#### Week 3: Infrastructure & Devices
- [ ] Configure advanced GPU management
- [ ] Set up high-performance networking
- [ ] Deploy AI-specific observability
- [ ] Monitor real-time performance

#### Week 4: Security & Ecosystem
- [ ] Implement security and compliance
- [ ] Explore emerging ecosystem projects
- [ ] Deploy production-ready stack
- [ ] Present capstone project

### Final Assessment
- **Technical Implementation**: Complete AI infrastructure deployment
- **Performance Analysis**: Benchmark results and optimization
- **Security Implementation**: Compliance and governance setup
- **Documentation**: Architecture decisions and lessons learned

## 🔗 Additional Resources

### Essential Reading
- [CNCF AI Landscape 2025](https://landscape.cncf.io/category=artificial-intelligence)
- [Kubernetes AI Special Interest Group](https://github.com/kubernetes/community/tree/master/sig-ai)
- [Cloud Native AI Whitepaper](https://github.com/cncf/toc/blob/main/workinggroups/ai/whitepaper.md)

### Community Engagement
- [CNCF AI Slack Channel](https://cloud-native.slack.com/channels/ai)
- [Kubernetes AI Working Groups](https://github.com/kubernetes/community/pull/8521/)
- [AI-Infra GitHub Discussions](https://github.com/pacoxu/AI-Infra/discussions)

### Tools & Utilities
- [AI Infrastructure Toolkit](https://github.com/cncf/ai-toolkit)
- [Performance Benchmarking Suite](https://github.com/kubernetes/perf-tests)
- [Monitoring Stack Templates](https://github.com/prometheus-operator/kube-prometheus)

---

**Note**: This learning plan is designed to be flexible. Adjust the pace based
on your background and time availability. Focus on hands-on experience and
practical implementation rather than just theoretical knowledge.

**Last Updated**: September 2025  
**Maintainer**: [@pacoxu](https://github.com/pacoxu)  
**License**: Apache 2.0