---
status: Active
maintainer: pacoxu
last_updated: 2025-12-03
tags: kubernetes, scalability, ant-group, api-server, etcd, large-scale
---

# 蚂蚁大规模集群经验：2万节点内存降低50%

本文介绍蚂蚁集团在大规模 Kubernetes 集群运营中的实践经验，涵盖 Etcd
拆分、控制面优化、API Server 内存优化等关键技术，实现了显著的性能提升和资源节约。

## 目录

- [蚂蚁大规模 Sigma 集群 Etcd 拆分实践（2022年）](#蚂蚁大规模-sigma-集群-etcd-拆分实践2022年)
- [蚂蚁集团大规模 Kubernetes 服务在数智时代的突破与重构](#蚂蚁集团大规模-kubernetes-服务在数智时代的突破与重构)
- [零侵入架构：超大规模 K8s 集群中 API Server 内存占用降低 50%
  的实战优化](#零侵入架构超大规模-k8s-集群中-api-server-内存占用降低-50-的实战优化)
- [关键收益](#关键收益)
- [参考资料](#参考资料)

## 蚂蚁大规模 Sigma 集群 Etcd 拆分实践（2022年）

蚂蚁在 2022 年进行了大规模 Sigma 集群的 Etcd 拆分实践，这是应对超大规模
Kubernetes 集群挑战的重要里程碑。

**原文链接**:
[蚂蚁大规模 Sigma 集群 Etcd 拆分实践](https://mp.weixin.qq.com/s/zJFaxMbwVjd_bReEWtiP2Q)

### 背景与挑战

蚂蚁业务混合了流式计算、离线计算和在线业务，面临以下挑战：

1. **短生命周期 Pod 数量巨大**: 单集群每天创建数十万个 Pod，
   大量生命周期在分钟级甚至秒级的 Pod，都需要 etcd 来支撑
2. **复杂的业务请求**: 大量的 List (list all、list by namespace、
   list by label)、watch、create、update、delete 请求
3. **性能衰减严重**: 这些请求性能会随着 etcd 存储规模增大而严重衰减，
   甚至导致 etcd OOM、请求超时等异常
4. **运维操作影响**: Compact、defrag 操作导致请求 RT P99 暴涨，
   甚至请求超时，造成集群关键组件（调度器、CNI 服务等 Operator）间断性丢失，
   导致集群不可用

![Traditional Pods data Etcd splitting process](https://github.com/user-attachments/assets/9793600c-0c84-48bc-8806-d9ce5039de2f)

### 拆分方案

传统 Pods 数据的 Etcd 拆分过程：

1. **集群禁止写操作**: APIServer 停机、数据关联组件停机、
   删除权限绑定 clusterrolebinding
2. **关键数据备份**: 备份 Etcd 数据等
3. **Etcd 数据拆分**: 使用 make-mirror 工具做数据迁移、
   通过校验 keys 的数量保证数据完整性
4. **Pods 数据迁移新 Etcd**: APIServer 更新配置重启、
   恢复之前删除的权限绑定、数据关联组件启动，恢复正常服务
5. **集群恢复**: 整个过程人工操作，耗时大约 1-2 个小时，人员 5-10 人
6. **通知业务恢复验证**: 期间集群因关键组件停机而功能不可用、
   数据校验手段薄弱

![Optimized Etcd splitting process without component shutdown](https://github.com/user-attachments/assets/ad0a0bc3-8214-46cc-977f-befee8cea95c)

### 优化后的流程

从组件不停机发送思考拆分流程：

1. **集群禁止 Pod 写操作**: 组件不停机
2. **Etcd 数据拆分 (Pod)**: 自动化完成数据迁移并新建 etcd 集群
3. **完整 Pods 数据迁移新 Etcd**: 允许写操作，集群即恢复服务
4. **集群允许 Pod 写操作**: 无需和业务大量沟通、关键过程自动化操作、
   耗时估算就是数据 Copy 的实际，约 10min，只剩 1 人

收益：

- 无需和业务大量沟通
- 关键过程自动化操作
- 耗时估算就是数据 Copy 的实际，约 10min
- 只剩 1 人

![Etcd splitting architecture comparison](https://github.com/user-attachments/assets/931f707b-4654-4d33-8c87-6138469feb68)

## 蚂蚁集团大规模 Kubernetes 服务在数智时代的突破与重构

**演讲者**: 谭崇康（见云）

**视频链接**:
[云原生论坛-2 蚂蚁集团大规模 Kubernetes 服务在数智时代的突破与重构](https://www.bilibili.com/video/BV1orUYBVEqE)

### 一、在数智快车上，K8s 承担什么角色

#### 智能应用飞速发展

根据 Spectro Cloud 的 2025 年生产 Kubernetes 报告，AI 应用正在快速增长：

- **90%** 的企业预计在未来 12 个月内在 Kubernetes
  上运行更多的 AI 工作负载，AI 是增长最快的趋势
- **88%** 报告 Kubernetes TCO 同比增长，成本是采用者面临的首要挑战
- **50%** 现在在边缘运行 Kubernetes 生产环境，由 AI 工作负载驱动
- **51%** 仍将集群作为"雪花"运行，高度手动操作，尽管 80%
  采用了平台工程实践

![Spectro Cloud 2025 Kubernetes report statistics](https://github.com/user-attachments/assets/c9357990-d4c0-4364-a735-49d25667aa64)

#### AI 应用框架如何与 K8s 交互

从常用的 AI 应用框架，我们能看到：

- AI 应用框架如何与 K8s 交互
- 研发这些 AI 框架 Operator 的工程师真的非常了解如何面向 Kubernetes
  的编程吗？

主流框架：

| 框架 | 核心研发语言 | K8s 适配方式 | 核心定位 |
|------|------------|-------------|---------|
| TensorFlow | C++ (底层)、Python (API) | TensorFlow Operator | 通用深度学习（训练 + 推理）|
| PyTorch | C++ (底层)、Python (API) | PyTorch Operator | 灵活深度学习（科研 + 工业）|
| Kubeflow | Go (核心)、Python (SDK) | 原生 K8s CRD/Operator | AI 工作流编排（CNCF 孵化）|
| MLflow | Python (核心) | Docker 镜像 + K8s 部署 | ML 生命周期管理 |
| Ray | C++ (底层)、Python | Ray Operator | 分布式 AI 计算（CNCF 沙箱）|
| Horovod | C++ (核心)、Python | 适配 Kubeflow/Operator | 多框架分布式训练 |
| KFServing | Go (核心)、Python | InferenceService CRD | 云原生推理服务（Kubeflow 生态）|
| TorchServe | Java (核心)、Python | Deployment/Helm | PyTorch 官方推理服务 |

![AI framework Kubernetes integration table](https://github.com/user-attachments/assets/ac4cbc01-35bf-4332-b2ed-a5bc98cfaba9)

#### 一些"哭笑不得"的设计和使用问题

Kubernetes 远不是一个 0 成本使用的服务。

常见问题：

- 不合理的资源请求和限制设置
- 过度的 List/Watch 操作
- 不理解 Kubernetes 的编程模型
- 缺乏对控制面压力的认知

![Common Kubernetes design and usage issues](https://github.com/user-attachments/assets/e2b39d88-17f0-46ca-a908-863961175b33)

#### 基础设施如何让这辆赛车更富竞争力

Meta 宣称在训练 OPT-175B 模型的两个星期时间段内因为硬件、基础设施或实验
稳定性问题而重新启动了 35 次。在开放的日志中也可以看到，
几乎整个训练过程都要面对不停地重启和中断。

### 二、数智应用的 K8s 服务需要满足什么特性

#### 规模要求

大一些，再大一些！规模是由哪些因素决定的？

- 节点规模：20,000+ 节点
- Pod 规模：每天创建数十万 Pod
- 请求规模：海量的 API 请求

#### 稳定性要求

稳，再稳一些，别添乱。为赛车搭配合适的基建和轮胎，
做好一个匹配智算应用计算需求的 Kubernetes 服务。

![K8s service characteristics for digital intelligence applications](https://github.com/user-attachments/assets/5164d859-7f4c-4a43-97b6-5a3d87a8a199)

### 三、怎样建设一个与之匹配的 K8s 服务

#### 怎样让大规模集群"稳"：可以是大象，但是不能臃肿

**稳定 = 规范管控 + 合理的饱和度 + 故障自愈**

##### 规范管控

- **KoM 架构**：Kubernetes on Mesh（后面会详细介绍）
- **多维度精细化限流**：保护控制面
- **统一接入标准化管控**：规范化 API 使用

##### 合理的系统饱和度

关键收益：

- **内存降低 50%**
- **CPU 降低 30%**
- **ETCD 存储水位降低 20%**
- **请求吞吐提升 40%**

##### 完善的自愈能力

- **Controller 自愈**：自动恢复故障的控制器
- **节点自愈**：自动处理节点故障

#### 怎样让大规模集群"稳"：服务托管

**KCS（K8sControllerStack）让 Controller 编程更简单**

关键技术：

- WarmCache：预热缓存
- 长尾请求管理：处理慢请求
- 主动感知故障/主动自愈：快速恢复
- 观测诊断等技术：全面监控

收益：

- **切主耗时 10min → 10s**
- **Watch 延迟 P99 < 1s**
- **请求成功率 99.9%**

#### 怎样让大规模集群"稳"：独立执行环境

**应用 Cell 化管理，应用独立执行互不干扰**

CELL 化独立的执行环境，提供混布集群更高用户隔离能力：

- **ApiResourceLimiter**：对 ApiServer 的 API 请求 Quota，
  包含用户请求以及系统为用户提供服务发起的请求
- **ResourceCell**：用户资源视图。保障平台方只能看见平台方自己创建的资源
- **ETCDStorageLimiter**：可以使用的 ETCD 存储对象的个数和大小
- **SystemCapacities**：独立的系统功能，例如调度、DNS、网络模式等

#### 如何让大象也能跳舞：极速 API 链路

**MVCC ReadCache/NPKV/动态索引等优化**

收益：

- **ETCD 性能读延迟 P99 降低 51%，写延迟 P99 降低 32%**
- **ApiServer 吞吐提升 30%+，Event 降低 90%+，Watch 延迟 P99 < 1s**
- **Controller CPU 利用率降低 50%+，Memory 降低 66%，
  Watch 延迟降低 P99 < 1s**

![Ultra-fast API chain optimization results](https://github.com/user-attachments/assets/9529ab59-7866-4ae3-a931-9480569b77de)

#### KubeSpeed 容器极速交付链路

**KubeSpeed 容器加速技术，支持 Sandbox、镜像、Pod 缓存等多维加速能力**

收益：

- **应用启动耗时降低 95%**

#### 容器交付保障

**TKP (TurnKeyResourceProvision) 容器交付托管**

TKP 容器托管技术支持容器（Workload）创建、删除托管

收益：

- **创建成功率提升 2%**
- **删除成功率提升 3%**
- **大幅节省创建/删除过程中的计算卡时浪费**

#### 资源供应保障

**TKP 大规格及跨集群资源交付托管**

TKP 大规格 ReplaceQuota 技术及跨集群交付技术

收益：

- **大规格耗时长 Pod 比例降低 90%**
- **支持丰富的多集群资源供给能力**

#### 问题诊断及自愈

**Lunettes E2E 容器自助诊断服务**

端到端的诊断到自愈链路，L1 拦截率提升至 80%+

能力：

- Log/Event/Audit 等多维度数据构建端到端的问题诊断能力
- 应用、模型、容器、SLO 等全域场景支持
- Metrics、Trace 的各种形式下钻能力
- 打通诊断+自愈全链路，提升用户自助能力

### 四、一些实践经验

#### Kubernetes 版本升级收益

| 收益项 | 具体说明 |
|--------|---------|
| 安全性提升 | 社区修复大量漏洞，加强 RBAC、Webhook、Secret 等安全措施， 有效降低安全风险 |
| 新功能与优化 | 新版本支持更多高级功能，如 DRA、网络策略、资源扩展、 服务网格等 |
| 性能与稳定性提高 | 控制面和调度器更优化，节点和负载管理性能提升 |
| 第三方生态兼容性提升 | 与主流 DevOps、监控、服务网格等工具插件全面兼容， 可用新版本生态插件 |
| 运维便利性提高 | 更完善的集群管理资源、调优参数、自动运维特性提升 |
| 更长生命周期与支持 | 新版本获得社区和第三方长期支持， 降低技术债务和维护压力 |

## 零侵入架构：超大规模 K8s 集群中 API Server 内存占用降低 50% 的实战优化

**演讲者**: 明廷樟

**视频链接**: [KCD 杭州【蚂蚁集团】云原生论坛-9 零侵入架构：
超大规模 K8s 集群中 API Server 内存占用降低 50%
的实战优化](https://www.bilibili.com/video/BV1R1UYB6EN2/)

![API Server memory optimization presentation title](https://github.com/user-attachments/assets/aec823cb-f439-42fd-ace9-090707a7c17c)

![API Server memory optimization presentation agenda](https://github.com/user-attachments/assets/a793803a-4418-4d37-9808-2644c89b95f5)

### 一、背景：超大规模 k8s 集群挑战

#### 业务影响

kube-apiserver 的稳定性对业务有直接影响

#### 资源压力

面临巨大的资源（内存、单机等）压力

![Ultra large-scale K8s cluster challenges](https://github.com/user-attachments/assets/ff3b57c4-40b2-4d82-8799-0e0f79901d7b)

#### 资源耦合风险

**背景**: 所有资源类型（Pod、Service、CRD 等）共享 Apiserver 实例，
资源保障等级不一

**风险**: 非核心资源（Event）挤占核心资源（Pod）处理能力

**案例**: Event 流量导致整个集群出现雪崩

### 二、方案：架构升级 - 分而治之

#### 整体思路：分而治之

![Divide and conquer architecture diagram](https://github.com/user-attachments/assets/5c2f4733-9fd2-4c67-be30-2a83993728ee)

#### 理论基础：apiserver 内部 watch cache 逻辑

要点：

1. **Watch Cache**: apiserver 会对所有资源粒度从 etcd 缓存到本地
2. **逻辑**: 如果某个资源没有 watch cache，则会直接打穿到 etcd

#### 理论基础：按照资源类别的请求分析

要点：

1. **节约内存资源**: pod 分组 apiserver 只需要 cache pod 资源的数据

### 三、技术方案：流量按资源进行路由

![Traffic routing by resource type](https://github.com/user-attachments/assets/5613a03b-fef1-45e3-8c7f-0714739371c9)

#### 技术方案：网关 kok (kubernetes on kubernetes) → kom (kubernetes on mesh)

**kom 网关特性**：

- 单集群流量入口
- 无感升级能力

#### 技术方案：资源拆分分组

**分组策略**：

1. **Pod 分组**: 交付核心资源，独占
2. **Config 分组**: 配置类资源，包括 nodes/configmaps/leases/secrets 等资源
3. **Event 分组**: 非交付链路资源
4. **Default 分组**: cache 所有资源，一旦任何异常，可将流量回切至该分组

#### 技术方案：apiserver 分组

**关键参数**：

1. `--default-watch-cache-size`: 默认的 watch cache size 大小
2. `--watch-cache-sizes`: 对应资源的 watch cache 个数，
   例如 `endpoints#0,endpointslices.discovery.k8s.io#0,nodes#0`

#### 技术方案：灰度无感丝滑升级

**流程**：

1. 新建其他（pod）分组
2. 将流量按照 useragent 将客户端从原有 apiserver（default 分组）灰度切流

### 四、总结：收益及问题总结

#### 收益

##### Apiserver: 实例个数不变的情况下，平均内存下降 50%

![Apiserver memory reduction results](https://github.com/user-attachments/assets/6dc65145-258b-4c3a-a5de-b9933252d1ca)

##### Etcd 性能：CPU seconds 下降 40%

![Etcd performance CPU reduction results](https://github.com/user-attachments/assets/32ee9c5e-65d8-4f09-92bf-58bc81c4ef20)

#### 上线过程中遇到的一些问题

##### 问题 1：event apiserver 分组从 etcd list all pods

**原因**:

- node 鉴权/TokenRequest featuregate 开启会导致 list all pods

##### 问题 2：apiserver 会周期性调用 etcd 进行 count key

**解决**: `--etcd-count-metric-poll-period=0`

##### 问题 3：kom 网关上线遇到的一些问题

1. **网关 Stream error 偶发断连问题**
   - 调整 keep alive 配置

2. **H2 flow control 导致的部分请求 rt**
   - 调整 H2 流控配置

### 五、展望：未来的一些思路

**要点**:

1. 将 pod 资源彻底从不需要的分组中去除掉，会进一步提升 apiserver/etcd 性能
2. Controller 类组件同样面临巨大的内存压力，缺乏水平扩展能力

## 关键收益

### 整体性能提升

| 指标 | 提升幅度 |
|------|---------|
| API Server 内存 | **降低 50%** |
| CPU 使用 | **降低 30%** |
| ETCD 存储水位 | **降低 20%** |
| 请求吞吐 | **提升 40%** |
| ETCD 读延迟 P99 | **降低 51%** |
| ETCD 写延迟 P99 | **降低 32%** |
| API Server 吞吐 | **提升 30%+** |
| Event 数量 | **降低 90%+** |
| Watch 延迟 P99 | **< 1s** |
| Controller CPU | **降低 50%+** |
| Controller Memory | **降低 66%** |
| 应用启动耗时 | **降低 95%** |
| 切主耗时 | **10min → 10s** |
| 请求成功率 | **99.9%** |

### 架构优化

- **KoM (Kubernetes on Mesh)**: 网关统一流量入口，无感升级
- **资源分组**: Pod、Config、Event、Default 分组，隔离资源影响
- **Watch Cache 优化**: 按需缓存，减少内存占用
- **CELL 化管理**: 独立执行环境，用户隔离

### 容器交付优化

- **KubeSpeed**: Sandbox、镜像、Pod 缓存多维加速
- **TKP**: 容器交付托管，创建成功率提升 2%，删除成功率提升 3%
- **大规格 Pod**: 耗时长 Pod 比例降低 90%

### 诊断与自愈

- **KCS**: Controller 编程简化，切主耗时 10min → 10s
- **Lunettes**: E2E 诊断服务，L1 拦截率提升至 80%+

## 参考资料

1. [蚂蚁大规模 Sigma 集群 Etcd 拆分实践（2022年）](https://mp.weixin.qq.com/s/zJFaxMbwVjd_bReEWtiP2Q)
2. [云原生论坛-2 蚂蚁集团大规模 Kubernetes 服务在数智时代的突破与重构
   - 谭崇康（见云）](https://www.bilibili.com/video/BV1orUYBVEqE)
3. [KCD 杭州【蚂蚁集团】云原生论坛-9 零侵入架构：
   超大规模 K8s 集群中 API Server 内存占用降低 50% 的实战优化
   - 明廷樟](https://www.bilibili.com/video/BV1R1UYB6EN2/)
4. [Spectro Cloud - 2025 State of Production Kubernetes
   Report](https://www.spectrocloud.com/news/2025-state-of-production-kubernetes-report)

## 相关文档

- [Large-Scale Kubernetes Clusters](../../kubernetes/large-scale-clusters.md)
- [Scheduling Optimization](../../kubernetes/scheduling-optimization.md)
- [Workload Isolation](../../kubernetes/isolation.md)
