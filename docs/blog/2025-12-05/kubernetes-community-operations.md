---
status: Active
maintainer: pacoxu
date: 2025-12-05
tags: kubernetes, community, open-source, ai, ml, contribution
canonical_path: docs/blog/2025-12-05/kubernetes-community-operations.md
---

# How the Kubernetes Community Operates: Entry Points in the AI Era

## Introduction

As of November 2025, the Kubernetes community has grown to an incredible
scale: **97,800 contributors**, **4.63 million contributions**, and **8,600
code reviewers** participating in the project. This vibrant ecosystem
continues to evolve, especially with the rapid growth of AI/ML workloads that
are pushing Kubernetes into new territories.

This post explores how the Kubernetes community is structured, how it
operates, and most importantly, where newcomers can find entry points in the
AI era.

## Community Structure Overview

The Kubernetes community operates under the Cloud Native Computing Foundation
(CNCF), a non-profit organization that provides funding, guidance, and various
services to the project.

![Community Structure](https://github.com/user-attachments/assets/fa6ad7ad-b28e-4f2d-8ffc-60fb09e3f604)

The community is organized hierarchically:

### 1. Cloud Native Computing Foundation (CNCF)

- Non-profit organization that Kubernetes is part of
- Provides and manages funding and various guidance and services
- Ensures project sustainability and vendor neutrality

### 2. Steering Committee

- **7 Members** elected by Kubernetes Organization Members
- Interfaces with CNCF
- Has whole-project scope
- Sets the strategic direction for the project

### 3. SIGs / WGs (Special Interest Groups / Working Groups)

- **Work Areas within Kubernetes**
- Examples: Networking, Release, Docs, etc.
- **SIGs = constant**: Long-term ownership areas
- **WGs = topical/temporary**: Time-bound initiatives

### 4. Subprojects

- Created by SIGs
- Groups that execute on specific work/projects
- Focused implementation teams

## The Contributor Ladder

Understanding the contributor ladder helps you plan your journey in the
Kubernetes community:

![The Contributor Ladder](https://github.com/user-attachments/assets/ef2fc1d0-5088-4e23-9597-b94129e76db0)

### Non-member Contributors (You Are Here!)

- Anyone can start contributing to Kubernetes
- No membership required to submit code or documentation

### Member

- **Active contributor** to the project
- **Sponsored by two Reviewers**
- Has voting rights in the community
- Can trigger CI jobs and use `/lgtm` command

### Reviewer

- **History of reviewing** frequently
- **Authorship in subproject**
- Approves code quality and style
- Can use `/lgtm` (looks good to me) command

### Approver

- **Approve contributions for acceptance**
- **Highly experienced reviewer and contributor** in subproject
- Has deep understanding of code architecture
- Can use `/approve` command

### Subproject Owner

- **Subject matter expert** for repository/directory
- **Highly experienced**, aids in triage and mentorship for scoped area
- Makes architectural decisions for their area

### Subproject Lead

- **Set priorities and approve proposals** for subproject
- **Responsibility and leadership** for entire project across all
  repos/directories
- Coordinates with other subprojects and SIGs

### SIG Chair / Tech Lead

- **Set priorities and manage** the SIG and its subprojects
- **Interface with the Steering Committee**
- Represent the SIG in community-wide discussions

**Learn more about Org Membership**:
<https://github.com/kubernetes/community/blob/master/community-membership.md>

## Current SIGs, WGs, and Committees

As of late 2024, the Kubernetes community has evolved its organizational
structure to better address modern challenges:

![Kubernetes Community Structure](https://github.com/user-attachments/assets/c1bae44e-52fc-41c2-9b67-a965ae88ee58)

### Project-Level Groups

- **Architecture**: System design and evolution
- **Contributor Experience**: Improving contributor workflows
- **Docs**: Documentation and website
- **Security Response**: Security vulnerability handling

### Committees

- **Code of Conduct**: Community behavior standards
- **Steering**: Overall project governance

### Horizontal SIGs (Cross-cutting concerns)

- **API Machinery**: Core API infrastructure
- **Auth**: Authentication and authorization
- **CLI**: Command-line tools (kubectl)
- **Instrumentation**: Metrics and monitoring
- **Windows**: Windows container support
- **Structured Logging**: Logging infrastructure
- **Long Term Support (LTS)**: Long-term support strategy
- **AI Conformance**: AI workload conformance testing

### Vertical SIGs (Feature areas)

- **Apps**: Application lifecycle management
- **Autoscaling**: Horizontal and vertical pod autoscaling
- **Cloud Provider**: Cloud provider integrations
- **Cluster Lifecycle**: Cluster creation and management
- **Storage**: Persistent storage solutions
- **etcd**: Key-value store operations
- **Network**: Networking features and CNI
- **Node**: Node lifecycle and resource management
- **Scheduling**: Pod scheduling and resource allocation

### Working Groups (Temporary/Topical)

- **Checkpoint Restore**: Container checkpointing
- **Node Lifecycle**: Node operations and lifecycle
- **AI Gateway**: AI inference gateway solutions
- **AI Integration**: AI workload integration
- **Device Management**: Hardware device management
- **etcd Operator**: etcd operator development
- **Batch**: Batch processing workloads
- **Serving**: Serving workloads (inference)
- **Data Protection**: Data backup and recovery

**New Working Groups indicate emerging areas** with active development and
opportunities for contribution.

## AI/ML Entry Points in Kubernetes

The rapid growth of AI/ML workloads has created exciting new opportunities in
the Kubernetes community. Here are the key working groups focused on AI/ML:

![AI/ML Working Groups](https://github.com/user-attachments/assets/504acacc-77a6-43dc-b5d4-ff243e7d0b68)

### WG Batch and Serving: Workload-centric

These working groups focus on the fundamental workload patterns for AI/ML:

- **WG Batch**: Training workloads, distributed training, gang scheduling
- **WG Serving**: Inference workloads, model serving, autoscaling

**Key initiatives:**

- JobSet for distributed training coordination
- LeaderWorkerSet for inference workloads
- Gang scheduling for all-or-nothing placement
- Dynamic resource allocation for GPUs

### WG Device Management: Hardware-driven

Focuses on managing specialized hardware for AI workloads:

- GPU management and sharing
- TPU integration
- Custom accelerator support
- Dynamic Resource Allocation (DRA) API

**Key technologies:**

- NVIDIA GPU Operator
- Node Resource Interface (NRI)
- Device Plugin framework evolution
- DRA drivers and resource claims

### WG AI Conformance: Bird's-eye view

Provides a holistic view of AI workload compatibility:

- Conformance testing for AI workloads
- Best practices for AI on Kubernetes
- Integration patterns validation
- Performance benchmarking

### WG AI Gateway: Product-driven

Focuses on production AI deployment patterns:

- API gateway for LLM inference
- Multi-model serving
- Traffic routing and load balancing
- Cost optimization strategies

### WG AI Integration: Cross-cutting

The umbrella group coordinating AI efforts:

- Coordinates between all AI-related working groups
- Ensures consistent APIs and patterns
- Drives community alignment
- Identifies gaps and opportunities

**Relationships:**

- WG Batch and WG Serving feed into WG AI Integration
- WG Device Management provides infrastructure for all workloads
- WG AI Gateway builds on WG Serving patterns
- WG AI Conformance validates solutions from all groups

## Getting Started: New Contributor Orientation

The Kubernetes community offers excellent resources for new contributors:

### New Contributor Orientation

**Official Guide**:
<https://github.com/kubernetes/community/tree/master/mentoring/new-contributor-orientation>

The orientation program includes:

1. **Understanding the Project**
   - Project history and governance
   - Community values and code of conduct
   - Communication channels (Slack, mailing lists, meetings)

2. **Technical Onboarding**
   - Development environment setup
   - Testing infrastructure
   - CI/CD pipeline understanding

3. **Contribution Workflow**
   - Finding good first issues
   - Pull request process
   - Code review expectations
   - Working with SIGs

4. **Community Engagement**
   - Attending SIG meetings
   - Participating in discussions
   - Finding mentors
   - Building relationships

### Resources for AI/ML Contributors

If you're interested in AI/ML workloads on Kubernetes:

1. **Join relevant Slack channels**
   - #wg-batch
   - #wg-serving
   - #wg-device-management
   - #sig-scheduling
   - #sig-node

2. **Attend WG meetings**
   - Check the community calendar: <https://kubernetes.dev/>
   - Meetings are open to everyone
   - Great way to understand current priorities

3. **Explore good first issues**
   - Look for `good-first-issue` labels
   - AI-related repositories often need documentation
   - Testing and validation are always needed

4. **Follow AI/ML initiatives**
   - Dynamic Resource Allocation (DRA)
   - Gang Scheduling
   - LeaderWorkerSet (LWS)
   - JobSet
   - AI conformance testing

## Many More Initiatives

The Kubernetes community is incredibly active with numerous ongoing
initiatives beyond what we've covered. The AI/ML space continues to evolve
rapidly with new proposals, enhancements, and integrations being discussed
regularly.

Some areas to watch:

- **Serverless AI inference** patterns
- **Multi-tenancy** for AI workloads
- **Cost optimization** for GPU workloads
- **Observability** for distributed training
- **Security** for AI models and data
- **Edge AI** deployment patterns

## Conclusion

The Kubernetes community provides a well-structured, inclusive environment for
contributors at all levels. With the explosive growth of AI/ML workloads, there
are more opportunities than ever to make meaningful contributions.

Whether you're interested in core scheduling improvements, GPU management,
distributed training, or inference serving, there's a place for you in the
Kubernetes community.

**Start your journey today:**

- Visit <https://kubernetes.dev/> for community resources
- Join the Slack workspace
- Pick a working group aligned with your interests
- Say hello and start contributing!

## References

- **Kubernetes Community**: <https://kubernetes.dev/>
- **New Contributor Orientation**:
  <https://github.com/kubernetes/community/tree/master/mentoring/new-contributor-orientation>
- **Community Membership**:
  <https://github.com/kubernetes/community/blob/master/community-membership.md>
- **Kubernetes 开源入门手册**:
  <https://mp.weixin.qq.com/s/-htUKeQLF6_m6_bQjDxGMw>
- **Kubernetes社区是如何运作的**:
  <https://mp.weixin.qq.com/s/KS0IGr8XeNwcWTgl9AFAUg>

---

*This blog post is part of the AI-Infra learning path. For more resources on
AI infrastructure and Kubernetes, visit the [main repository](../../../README.md).*
