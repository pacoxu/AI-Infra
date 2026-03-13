---
status: Active
maintainer: pacoxu
last_updated: 2025-12-03
tags: kubernetes, scalability, ant-group, api-server, etcd, large-scale
---

# Ant Group Large-Scale Cluster Experience: 50% Memory Reduction at
20K Nodes

This article introduces Ant Group's practical experiences in operating
large-scale Kubernetes clusters, covering Etcd splitting, control plane
optimization, API Server memory optimization and other key technologies,
achieving significant performance improvements and resource savings.

## Table of Contents

- [Ant Group's Large-Scale Sigma Cluster Etcd Splitting Practice
  (2022)](#ant-groups-large-scale-sigma-cluster-etcd-splitting-practice-2022)
- [Large-Scale Kubernetes Service Breakthroughs and Reconstruction in the
  Digital Intelligence Era](#large-scale-kubernetes-service-breakthroughs-and-reconstruction-in-the-digital-intelligence-era)
- [Zero-Intrusion Architecture: 50% API Server Memory Reduction in Ultra
  Large-Scale K8s Clusters](#zero-intrusion-architecture-50-api-server-memory-reduction-in-ultra-large-scale-k8s-clusters)
- [Key Benefits](#key-benefits)
- [References](#references)

## Ant Group's Large-Scale Sigma Cluster Etcd Splitting Practice (2022)

In 2022, Ant Group conducted large-scale Sigma cluster Etcd splitting
practice, which was an important milestone in addressing ultra-large-scale
Kubernetes cluster challenges.

**Original Article**:
[Ant Group's Large-Scale Sigma Cluster Etcd Splitting
Practice](https://mp.weixin.qq.com/s/zJFaxMbwVjd_bReEWtiP2Q) (Chinese)

### Background and Challenges

Ant Group's business mixes streaming computing, offline computing, and online
services, facing the following challenges:

1. **Massive Short-Lived Pods**: A single cluster creates hundreds of
   thousands of Pods daily, with many having lifecycles at the minute or even
   second level, all requiring etcd support
2. **Complex Business Requests**: Large volumes of List (list all,
   list by namespace, list by label), watch, create, update, delete requests
3. **Severe Performance Degradation**: These request performances degrade
   severely as etcd storage scales up, even causing etcd OOM,
   request timeouts and other anomalies
4. **Operational Impact**: Compact and defrag operations cause request RT P99
   spikes, even request timeouts, causing intermittent loss of critical
   cluster components (scheduler, CNI services, other Operators),
   leading to cluster unavailability

![Traditional Pods data Etcd splitting process](https://github.com/user-attachments/assets/9793600c-0c84-48bc-8806-d9ce5039de2f)

### Splitting Solution

Traditional Pods data Etcd splitting process:

1. **Cluster Write Prohibition**: APIServer shutdown,
   data-related component shutdown, delete permission binding clusterrolebinding
2. **Critical Data Backup**: Backup Etcd data, etc.
3. **Etcd Data Splitting**: Use make-mirror tool for data migration,
   verify data integrity by checking number of keys
4. **Pods Data Migration to New Etcd**: APIServer configuration update and
   restart, restore previously deleted permission bindings,
   data-related components start, restore normal service
5. **Cluster Recovery**: The entire process is manual,
   taking about 1-2 hours with 5-10 people
6. **Notify Business for Recovery Verification**: During this period,
   the cluster is unavailable due to critical component shutdown,
   and data verification methods are weak

![Optimized Etcd splitting process without component shutdown](https://github.com/user-attachments/assets/ad0a0bc3-8214-46cc-977f-befee8cea95c)

### Optimized Process

Rethinking the splitting process without component shutdown:

1. **Cluster Prohibit Pod Write Operations**: Components remain running
2. **Etcd Data Splitting (Pod)**: Automated data migration and new etcd
   cluster creation
3. **Complete Pods Data Migration to New Etcd**: Allow write operations,
   cluster immediately restores service
4. **Cluster Allow Pod Write Operations**: No need for extensive
   communication with business teams, key processes automated,
   estimated time is just the actual data Copy time, about 10min, only 1 person

Benefits:

- No need for extensive communication with business teams
- Key processes automated
- Estimated time is just the actual data Copy time, about 10min
- Only 1 person needed

![Etcd splitting architecture comparison](https://github.com/user-attachments/assets/931f707b-4654-4d33-8c87-6138469feb68)

## Large-Scale Kubernetes Service Breakthroughs and Reconstruction in the Digital Intelligence Era

**Speaker**: Tan Chongkang (Jianyun)

**Video Link**:
[Cloud Native Forum-2 Ant Group's Large-Scale Kubernetes Service
Breakthroughs and Reconstruction in the Digital Intelligence
Era](https://www.bilibili.com/video/BV1orUYBVEqE) (Chinese)

### 1. K8s Role in the Digital Intelligence Era

#### Rapid Growth of AI Applications

According to Spectro Cloud's 2025 State of Production Kubernetes report,
AI applications are growing rapidly:

- **90%** expect to run more AI workloads on Kubernetes in the next 12 months.
  AI is the top growth trend
- **88%** reported increased Kubernetes TCO year on year. Cost is the #1
  challenge facing adopters
- **50%** now run Kubernetes in production at the edge, driven by AI workloads
- **51%** still run clusters as 'snowflakes' with highly manual operations,
  despite 80% adopting platform engineering practices

![Spectro Cloud 2025 Kubernetes report statistics](https://github.com/user-attachments/assets/c9357990-d4c0-4364-a735-49d25667aa64)

#### How AI Application Frameworks Interact with K8s

From common AI application frameworks, we can see:

- How AI application frameworks interact with K8s
- Do the engineers developing these AI framework Operators really understand
  how to program for Kubernetes?

Mainstream frameworks:

| Framework | Core Dev Language | K8s Adapter | Core Positioning |
|-----------|------------------|-------------|------------------|
| TensorFlow | C++ (low-level), Python (API) | TensorFlow Operator | General deep learning (training + inference) |
| PyTorch | C++ (low-level), Python (API) | PyTorch Operator | Flexible deep learning (research + industry) |
| Kubeflow | Go (core), Python (SDK) | Native K8s CRD/Operator | AI workflow orchestration (CNCF Incubating) |
| MLflow | Python (core) | Docker image + K8s deployment | ML lifecycle management |
| Ray | C++ (low-level), Python | Ray Operator | Distributed AI computing (CNCF Sandbox) |
| Horovod | C++ (core), Python | Adapt Kubeflow/Operator | Multi-framework distributed training |
| KFServing | Go (core), Python | InferenceService CRD | Cloud-native inference service (Kubeflow ecosystem) |
| TorchServe | Java (core), Python | Deployment/Helm | PyTorch official inference service |

![AI framework Kubernetes integration table](https://github.com/user-attachments/assets/ac4cbc01-35bf-4332-b2ed-a5bc98cfaba9)

#### Some "Frustrating" Design and Usage Issues

Kubernetes is far from a zero-cost service to use.

Common issues:

- Unreasonable resource requests and limits settings
- Excessive List/Watch operations
- Lack of understanding of Kubernetes programming model
- Lack of awareness of control plane pressure

![Common Kubernetes design and usage issues](https://github.com/user-attachments/assets/e2b39d88-17f0-46ca-a908-863961175b33)

#### How Infrastructure Makes This Race Car More Competitive

Meta claimed that during the two-week period of training the OPT-175B model,
they had to restart 35 times due to hardware, infrastructure,
or experimental stability issues. The open logs also show that almost the
entire training process faced continuous restarts and interruptions.

### 2. What Characteristics K8s Services for Digital Intelligence
Applications Need

#### Scale Requirements

Bigger, even bigger! What factors determine scale?

- Node scale: 20,000+ nodes
- Pod scale: Hundreds of thousands of Pods created daily
- Request scale: Massive API requests

#### Stability Requirements

More stable, even more stable, don't cause trouble. Equip the race car with
suitable infrastructure and tires, build a Kubernetes service that matches
intelligent computing application computing needs.

![K8s service characteristics for digital intelligence applications](https://github.com/user-attachments/assets/5164d859-7f4c-4a43-97b6-5a3d87a8a199)

### 3. How to Build a Matching K8s Service

#### How to Make Large-Scale Clusters "Stable" Can Be an Elephant,
But Cannot Be Bloated

**Stability = Standardized Governance + Reasonable Saturation +
Fault Self-Healing**

##### Standardized Governance

- **KoM Architecture**: Kubernetes on Mesh (detailed later)
- **Multi-dimensional Fine-grained Rate Limiting**: Protect control plane
- **Unified Access Standardized Governance**: Standardize API usage

##### Reasonable System Saturation

Key benefits:

- **Memory reduced by 50%**
- **CPU reduced by 30%**
- **ETCD storage watermark reduced by 20%**
- **Request throughput increased by 40%**

##### Complete Self-Healing Capability

- **Controller Self-Healing**: Automatically recover failed controllers
- **Node Self-Healing**: Automatically handle node failures

#### How to Make Large-Scale Clusters "Stable" Service Hosting

**KCS (K8sControllerStack) Makes Controller Programming Simpler**

Key technologies:

- WarmCache: Cache prewarming
- Long-tail Request Management: Handle slow requests
- Proactive Fault Awareness/Self-Healing: Fast recovery
- Observation and Diagnostics: Comprehensive monitoring

Benefits:

- **Leader election time 10min → 10s**
- **Watch latency P99 < 1s**
- **Request success rate 99.9%**

#### How to Make Large-Scale Clusters "Stable" Independent Execution
Environment

**Application Cell Management, Independent Execution Without Interference**

CELL-based independent execution environment provides higher user isolation
in mixed deployment clusters:

- **ApiResourceLimiter**: API request Quota for ApiServer,
  including user requests and requests initiated by the system to provide
  services to users
- **ResourceCell**: User resource view. Ensures platform can only see
  resources created by the platform itself
- **ETCDStorageLimiter**: Number and size of ETCD storage objects that can
  be used
- **SystemCapacities**: Independent system functions, such as scheduling, DNS,
  network mode, etc.

#### How to Make Elephants Dance: Ultra-Fast API Chain

**MVCC ReadCache/NPKV/Dynamic Index and Other Optimizations**

Benefits:

- **ETCD performance read latency P99 reduced by 51%,
  write latency P99 reduced by 32%**
- **ApiServer throughput increased by 30%+, Event reduced by 90%+,
  Watch latency P99 < 1s**
- **Controller CPU utilization reduced by 50%+, Memory reduced by 66%,
  Watch latency P99 < 1s**

![Ultra-fast API chain optimization results](https://github.com/user-attachments/assets/9529ab59-7866-4ae3-a931-9480569b77de)

#### KubeSpeed Ultra-Fast Container Delivery Chain

**KubeSpeed Container Acceleration Technology, Supporting Multi-Dimensional
Acceleration Capabilities for Sandbox, Image, Pod Cache**

Benefits:

- **Application startup time reduced by 95%**

#### Container Delivery Assurance

**TKP (TurnKeyResourceProvision) Container Delivery Hosting**

TKP container hosting technology supports container (Workload) creation and
deletion hosting

Benefits:

- **Creation success rate increased by 2%**
- **Deletion success rate increased by 3%**
- **Significantly save computing card time waste during creation/deletion
  process**

#### Resource Supply Assurance

**TKP Large-Spec and Cross-Cluster Resource Delivery Hosting**

TKP large-spec ReplaceQuota technology and cross-cluster delivery technology

Benefits:

- **Long-duration large-spec Pod proportion reduced by 90%**
- **Support rich multi-cluster resource supply capabilities**

#### Problem Diagnosis and Self-Healing

**Lunettes E2E Container Self-Service Diagnostic Service**

End-to-end diagnostic to self-healing chain, L1 interception rate increased
to 80%+

Capabilities:

- Build end-to-end problem diagnosis capability with multi-dimensional data
  from Log/Event/Audit
- Full-domain scenario support for applications, models, containers, SLO, etc.
- Various drill-down capabilities for Metrics and Trace
- Connect diagnosis + self-healing full chain, improve user self-service
  capability

### 4. Some Practical Experiences

#### Kubernetes Version Upgrade Benefits

| Benefit Item | Specific Description |
|--------------|---------------------|
| Security Improvement | Community fixes numerous vulnerabilities, strengthens RBAC, Webhook, Secret and other security measures, effectively reduces security risks |
| New Features and Optimizations | New versions support more advanced features such as DRA, network policies, resource extensions, service mesh, etc. |
| Performance and Stability Improvement | Control plane and scheduler are more optimized, node and load management performance improved |
| Third-Party Ecosystem Compatibility Improvement | Fully compatible with mainstream DevOps, monitoring, service mesh and other tool plugins, can use new version ecosystem plugins |
| Operational Convenience Improvement | More complete cluster management resources, tuning parameters, automated operation and maintenance features |
| Longer Lifecycle and Support | New versions receive long-term support from community and third parties, reduce technical debt and maintenance pressure |

## Zero-Intrusion Architecture: 50% API Server Memory Reduction in Ultra Large-Scale K8s Clusters

**Speaker**: Ming Tingzhang

**Video Link**: [KCD Hangzhou [Ant Group] Cloud Native Forum-9
Zero-Intrusion Architecture: 50% API Server Memory Reduction in Ultra
Large-Scale K8s Clusters](https://www.bilibili.com/video/BV1R1UYB6EN2/)
(Chinese)

![API Server memory optimization presentation title](https://github.com/user-attachments/assets/aec823cb-f439-42fd-ace9-090707a7c17c)

![API Server memory optimization presentation agenda](https://github.com/user-attachments/assets/a793803a-4418-4d37-9808-2644c89b95f5)

### 1. Background: Ultra Large-Scale K8s Cluster Challenges

#### Business Impact

kube-apiserver stability has a direct impact on business

#### Resource Pressure

Facing enormous resource (memory, single machine, etc.) pressure

![Ultra large-scale K8s cluster challenges](https://github.com/user-attachments/assets/ff3b57c4-40b2-4d82-8799-0e0f79901d7b)

#### Resource Coupling Risk

**Background**: All resource types (Pod, Service, CRD, etc.) share Apiserver
instances, with different resource assurance levels

**Risk**: Non-core resources (Event) squeeze core resource (Pod) processing
capacity

**Case**: Event traffic causes entire cluster to avalanche

### 2. Solution: Architecture Upgrade - Divide and Conquer

#### Overall Approach: Divide and Conquer

![Divide and conquer architecture diagram](https://github.com/user-attachments/assets/5c2f4733-9fd2-4c67-be30-2a83993728ee)

#### Theoretical Foundation: apiserver Internal watch cache Logic

Key points:

1. **Watch Cache**: apiserver caches all resource granularities locally
   from etcd
2. **Logic**: If a resource has no watch cache, it will directly hit etcd

#### Theoretical Foundation: Request Analysis by Resource Category

Key points:

1. **Save Memory Resources**: pod-grouped apiserver only needs to cache pod
   resource data

### 3. Technical Solution: Route Traffic by Resource

![Traffic routing by resource type](https://github.com/user-attachments/assets/5613a03b-fef1-45e3-8c7f-0714739371c9)

#### Technical Solution: Gateway kok (kubernetes on kubernetes) →
kom (kubernetes on mesh)

**kom Gateway Features**:

- Single cluster traffic entry point
- Seamless upgrade capability

#### Technical Solution: Resource Split Grouping

**Grouping Strategy**:

1. **Pod Group**: Core delivery resources, exclusive
2. **Config Group**: Configuration-type resources,
   including nodes/configmaps/leases/secrets and other resources
3. **Event Group**: Non-delivery chain resources
4. **Default Group**: Cache all resources, can switch traffic back to this
   group in case of any anomaly

#### Technical Solution: apiserver Grouping

**Key Parameters**:

1. `--default-watch-cache-size`: Default watch cache size
2. `--watch-cache-sizes`: Corresponding resource watch cache count,
   e.g., `endpoints#0,endpointslices.discovery.k8s.io#0,nodes#0`

#### Technical Solution: Seamless Gradual Upgrade

**Process**:

1. Create new (pod) group
2. Gradually route traffic by useragent from original apiserver
   (default group)

### 4. Summary: Benefits and Issues Summary

#### Benefits

##### Apiserver: With Same Number of Instances, Average Memory Reduced by 50%

![Apiserver memory reduction results](https://github.com/user-attachments/assets/6dc65145-258b-4c3a-a5de-b9933252d1ca)

##### Etcd Performance: CPU seconds Reduced by 40%

![Etcd performance CPU reduction results](https://github.com/user-attachments/assets/32ee9c5e-65d8-4f09-92bf-58bc81c4ef20)

#### Issues Encountered During Launch

##### Issue 1: event apiserver Group Lists All Pods from etcd

**Cause**:

- Enabling node authentication/TokenRequest featuregate causes list all pods

##### Issue 2: apiserver Periodically Calls etcd for count key

**Solution**: `--etcd-count-metric-poll-period=0`

##### Issue 3: Some Issues Encountered During kom Gateway Launch

1. **Gateway Stream error Occasional Disconnection Issue**
   - Adjust keep alive configuration

2. **H2 flow control Causing Some Request rt Issues**
   - Adjust H2 flow control configuration

### 5. Outlook: Some Future Thoughts

**Key points**:

1. Completely removing pod resources from groups that don't need them will
   further improve apiserver/etcd performance
2. Controller-type components also face enormous memory pressure,
   lacking horizontal scaling capability

## Key Benefits

### Overall Performance Improvements

| Metric | Improvement |
|--------|-------------|
| API Server Memory | **Reduced by 50%** |
| CPU Usage | **Reduced by 30%** |
| ETCD Storage Watermark | **Reduced by 20%** |
| Request Throughput | **Increased by 40%** |
| ETCD Read Latency P99 | **Reduced by 51%** |
| ETCD Write Latency P99 | **Reduced by 32%** |
| API Server Throughput | **Increased by 30%+** |
| Event Count | **Reduced by 90%+** |
| Watch Latency P99 | **< 1s** |
| Controller CPU | **Reduced by 50%+** |
| Controller Memory | **Reduced by 66%** |
| Application Startup Time | **Reduced by 95%** |
| Leader Election Time | **10min → 10s** |
| Request Success Rate | **99.9%** |

### Architecture Optimizations

- **KoM (Kubernetes on Mesh)**: Gateway unified traffic entry,
  seamless upgrade
- **Resource Grouping**: Pod, Config, Event, Default groups,
  isolate resource impact
- **Watch Cache Optimization**: On-demand caching, reduce memory footprint
- **CELL Management**: Independent execution environment, user isolation

### Container Delivery Optimizations

- **KubeSpeed**: Multi-dimensional acceleration for Sandbox, image, Pod cache
- **TKP**: Container delivery hosting, creation success rate increased by 2%,
  deletion success rate increased by 3%
- **Large-Spec Pods**: Long-duration Pod proportion reduced by 90%

### Diagnostics and Self-Healing

- **KCS**: Simplified controller programming, leader election time 10min → 10s
- **Lunettes**: E2E diagnostic service, L1 interception rate increased to 80%+

## References

1. [Ant Group's Large-Scale Sigma Cluster Etcd Splitting Practice
   (2022)](https://mp.weixin.qq.com/s/zJFaxMbwVjd_bReEWtiP2Q) (Chinese)
2. [Cloud Native Forum-2 Ant Group's Large-Scale Kubernetes Service
   Breakthroughs and Reconstruction in the Digital Intelligence Era -
   Tan Chongkang (Jianyun)](https://www.bilibili.com/video/BV1orUYBVEqE)
   (Chinese)
3. [KCD Hangzhou [Ant Group] Cloud Native Forum-9 Zero-Intrusion
   Architecture: 50% API Server Memory Reduction in Ultra Large-Scale K8s
   Clusters - Ming Tingzhang](https://www.bilibili.com/video/BV1R1UYB6EN2/)
   (Chinese)
4. [Spectro Cloud - 2025 State of Production Kubernetes
   Report](https://www.spectrocloud.com/news/2025-state-of-production-kubernetes-report)

## Related Documentation

- [Large-Scale Kubernetes Clusters](../../kubernetes/large-scale-clusters.md)
- [Scheduling Optimization](../../kubernetes/scheduling-optimization.md)
- [Workload Isolation](../../kubernetes/isolation.md)
