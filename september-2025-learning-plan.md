# September 2025 AI-Infra Learning Plan 🎯

A focused monthly learning plan to advance your AI Infrastructure knowledge 
and stay current with the rapidly evolving landscape.

## 📅 Plan Overview

**Duration:** September 2025 (4 weeks)  
**Focus Areas:**
1. AI-Infra Concept Updates & Fundamentals
2. Repository Gap Analysis & New Topics
3. Project Release Tracking & Updates
4. Industry Events, Blogs & Community Insights

---

## 🎯 Week 1: AI-Infra Concept Updates & Fundamentals

### 📚 Core Concept Refresh

**Objective:** Update understanding of "What is AI Infrastructure" in 2025

#### Modern AI-Infra Definition (2025)
AI Infrastructure has evolved beyond traditional ML pipelines to encompass:

- **Edge-to-Cloud Continuum**: From edge inference to datacenter training
- **Disaggregated Architecture**: Separation of compute, storage, and 
  networking for AI workloads
- **Multi-Modal Support**: Infrastructure for text, image, audio, and 
  video models
- **Agentic Workflows**: Infrastructure supporting autonomous AI agents
- **Real-time Inference**: Ultra-low latency requirements for interactive AI

#### Key Architectural Shifts

**From Monolithic to Disaggregated:**
- Prefill/Decode separation in LLM serving
- Distributed KV cache management
- Model-specific resource allocation

**From Static to Dynamic:**
- AI-aware autoscaling (TTFT, TPOT metrics)
- Dynamic LoRA switching
- Context-aware request routing

### 📖 Learning Tasks

- [ ] **Monday-Tuesday**: Read updated AI-Infra landscape documentation
- [ ] **Wednesday**: Study disaggregated inference architectures
- [ ] **Thursday**: Review modern scheduling patterns (Gang, Multi-model)
- [ ] **Friday**: Explore AI Gateway concepts and implementations

### 🔗 Resources
- [AIBrix Architecture Overview](./inference/aibrix.md)
- [Prefill-Decode Disaggregation](./inference/pd-disaggregation.md)
- [Caching Mechanisms](./inference/caching.md)
- [Kubernetes Learning Plan](./kubernetes/kubernetes.md)

---

## 🕳️ Week 2: Repository Gap Analysis & Missing Topics

### 🎯 Objective
Identify and prioritize topics not yet covered in the AI-Infra repository.

### 🔍 Identified Gaps (High Priority)

#### 1. Model Quantization & Optimization
**Status:** Listed in "Coming Soon" - needs development
- **Topics:** INT8/FP16 quantization, GPTQ, AWQ, model compression
- **Projects:** AutoGPTQ, llm.c, DeepSpeed quantization

#### 2. AutoScaling Metrics & Strategies  
**Status:** Critical gap for production deployments
- **Metrics:** TTFT (Time to First Token), TPOT (Time per Output Token), 
  ITL (Inter-Token Latency)
- **Strategies:** Predictive scaling, queue-based scaling

#### 3. LLM Security & Compliance
**Status:** Emerging critical requirement
- **Topics:** Model security, prompt injection protection, PII handling
- **Projects:** NeMo Guardrails, LangKit

#### 4. Advanced Networking (RDMA, InfiniBand)
**Status:** Hardware-specific knowledge gap
- **Topics:** RDMA over Converged Ethernet (RoCE), GPU Direct
- **Relevance:** Multi-node training and large model serving

#### 5. Observability for LLM Workloads
**Status:** Specialized monitoring needs
- **Topics:** eBPF for LLM profiling, custom metrics collection
- **Projects:** Deepflow, LLM-specific Prometheus exporters

### 📝 Learning Tasks

- [ ] **Monday**: Research quantization techniques and tooling
- [ ] **Tuesday**: Study autoscaling metrics for LLM workloads  
- [ ] **Wednesday**: Explore LLM security frameworks and best practices
- [ ] **Thursday**: Investigate RDMA networking for AI workloads
- [ ] **Friday**: Review eBPF applications in LLM observability

### 🎯 Outcome
Create prioritized list of topics for future repository additions.

---

## 🚀 Week 3: Project Release Tracking & Updates

### 📊 Objective
Track new releases and updates from projects mentioned in the repository.

### 🔄 Key Projects to Monitor

#### Scheduling & Workloads
- **Kueue**: Monitor v0.9+ releases for improved gang scheduling
- **Volcano**: Track v1.10+ for enhanced GPU scheduling
- **LWS (LeaderWorkset)**: Follow graduation status and new features
- **DRA (Dynamic Resource Allocation)**: Monitor Kubernetes integration

#### Inference & Runtime  
- **vLLM**: Track major releases for performance improvements
- **AIBrix**: Monitor v0.5+ for new features and stability
- **SGlang**: Follow development for caching improvements
- **TorchServe**: Check for multi-model serving enhancements

#### AI Gateway & Orchestration
- **Gateway API Inference Extension**: Monitor Kubernetes SIG progress
- **Envoy AI Gateway**: Track development and feature releases
- **Istio**: Monitor AI/ML specific enhancements

#### Ecosystem Projects
- **Model Spec**: Follow CNCF Sandbox graduation progress
- **ImageVolume**: Monitor Kubernetes KEP implementation status

### 📅 Release Tracking Schedule

**Daily (10 minutes):**
- [ ] Check GitHub releases for 3-5 key projects
- [ ] Review CNCF TOC meetings for AI initiative updates

**Weekly:**
- [ ] Compile release notes summary
- [ ] Identify breaking changes or major features
- [ ] Update project status in repository documentation

### 🛠️ Tools for Tracking
- GitHub Watch notifications for key repositories
- CNCF TOC meeting notes
- Project community Slack channels
- Release RSS feeds

---

## 📰 Week 4: Industry Events, Blogs & Community Insights

### 🎯 Objective
Stay current with industry developments, conferences, and expert insights.

### 📅 September 2025 Events Calendar

#### Conferences & Meetups
- **KubeCon EU 2025 Follow-up**: Review AI Track sessions and recordings
- **AI_dev Conferences**: Track upcoming events and CFP announcements
- **GOSIM Events**: Monitor regional meetups and presentations
- **PyTorch Conference**: Follow announcements for infrastructure tracks

#### Community Events
- **CNCF AI Working Groups**: Attend relevant meetings
- **Kubernetes SIG Meetings**: Focus on Scheduling and Node SIGs
- **Local Meetups**: AI/ML infrastructure focused groups

### 📖 Blog & Content Curation

#### Key Sources to Monitor
- **Engineering Blogs**: Netflix, Uber, OpenAI, Anthropic infrastructure teams
- **CNCF Blog**: AI-related posts and project announcements
- **Kubernetes Blog**: AI/ML workload features and updates
- **Vendor Blogs**: NVIDIA, AMD, Intel AI infrastructure content

#### Content Categories
- **Architecture Deep Dives**: Disaggregated inference, distributed serving
- **Performance Studies**: Benchmarking, optimization case studies  
- **Operational Insights**: Production deployment experiences
- **Security Analysis**: AI-specific security challenges and solutions

### 📝 Learning Tasks

- [ ] **Monday**: Set up RSS feeds and monitoring for key sources
- [ ] **Tuesday-Wednesday**: Review 5-10 recent AI infrastructure blog posts
- [ ] **Thursday**: Watch 2-3 conference talks from recent events
- [ ] **Friday**: Summarize key insights and trends for the month

### 📊 Monthly Report Template

**New Concepts Learned:**
- List 3-5 new concepts or technologies discovered

**Project Updates:**
- Summarize major releases and their impact

**Industry Trends:**
- Identify 2-3 emerging trends in AI infrastructure

**Action Items:**
- List topics to explore further next month
- Repository updates needed
- New projects to investigate

---

## 🎯 Learning Outcomes & Success Metrics

### By End of September 2025:

#### Knowledge Gains
- [ ] Updated understanding of AI-Infra evolution and current state
- [ ] Comprehensive gap analysis of repository coverage
- [ ] Current awareness of project release cycles and updates
- [ ] Industry trend awareness and expert insights

#### Repository Contributions
- [ ] Documentation updates for key concepts
- [ ] New topic proposals for high-priority gaps
- [ ] Updated project status and release information
- [ ] Enhanced reference section with recent blogs and talks

#### Community Engagement  
- [ ] Active participation in 2-3 relevant community discussions
- [ ] Connections made with AI infrastructure practitioners
- [ ] Contributions to project discussions or issues

---

## 🔗 Quick Reference Links

### Daily Resources
- [CNCF Landscape - AI/ML Section](https://landscape.cncf.io/)
- [Kubernetes Enhancements Tracking](https://k8s.io/enhancements/)
- [AI-Infra Repository Issues](https://github.com/pacoxu/AI-Infra/issues)

### Weekly Compilations
- [Awesome LLMOps Updates](https://awesome-llmops.inftyai.com/)
- [CNCF AI Initiative Tracker](https://github.com/cncf/toc/issues?q=is%3Aissue+state%3Aopen+label%3Akind%2Finitiative)

### Community Channels
- CNCF Slack: #sig-ai, #ai-ml-workloads
- Kubernetes Slack: #sig-scheduling, #sig-node
- Project-specific Discord/Slack channels

---

## 📌 Notes

**Learning Approach:**
- Focus on hands-on experimentation where possible
- Balance depth vs. breadth based on current role needs
- Prioritize production-relevant topics over academic research
- Maintain learning log for reflection and future reference

**Time Management:**
- Allocate 5-7 hours per week for structured learning
- Use commute/travel time for blog reading and podcasts
- Schedule focused deep-dive sessions for complex topics
- Reserve Friday afternoons for reflection and note organization

**Community Contribution:**
- Share learnings through blog posts or repository updates
- Engage in project discussions with thoughtful questions
- Contribute documentation improvements where appropriate
- Mentor others in areas where you develop expertise

---

**Happy Learning! 🚀**

*This plan is designed to be flexible - adjust topics and timing based on 
your specific interests and current project needs.*