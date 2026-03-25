---
status: Active
maintainer: pacoxu
last_updated: 2025-12-17
tags: kubernetes, gpu, fault-detection, self-healing, observability, dcgm, ai-infrastructure
---

# Kubernetes GPU 故障检测与自愈实践指南

本文介绍 Kubernetes 集群中 GPU 硬件故障的检测、诊断和自动恢复方案，综合字节跳动火山、
微软 AKS 和 NVIDIA 的生产实践，为 AI Infra 工程师和 SRE 提供系统性的故障处理思路。

**注意：** 部分内容由 AI 辅助生成，使用前请仔细验证。

## 目录

- [为什么需要 GPU 故障自愈](#为什么需要-gpu-故障自愈)
- [四类常见 GPU 故障](#四类常见-gpu-故障)
- [故障检测方案](#故障检测方案)
- [三层故障语义模型](#三层故障语义模型)
- [渐进式自愈策略](#渐进式自愈策略)
- [故障感知调度](#故障感知调度)
- [作业级归因与计费](#作业级归因与计费)
- [生产部署建议](#生产部署建议)
- [参考资料](#参考资料)

## 为什么需要 GPU 故障自愈

在大规模 GPU 集群中运行 AI 训练和推理任务时，硬件故障是不可避免的：

- **训练中断损失大**：一次掉卡可能导致几天甚至几周的训练工作丢失
- **人工运维成本高**：凌晨收到告警，手动登录节点排查，影响睡眠和工作效率
- **误判影响可用性**：过于激进的故障响应会导致健康节点被错误下线
- **资源浪费严重**：故障 GPU 继续分配给新任务，导致任务反复失败

**核心目标：** 在保证集群健康的前提下，最小化对运行中任务的影响，自动化故障发现和恢复流程。

## 四类常见 GPU 故障

根据生产环境统计，GPU 故障主要分为四类：

### 1. 掉卡故障（最严重）

**现象：**

- GPU 从 nvidia-smi 输出中消失
- 驱动报告 "GPU has fallen off the bus"
- XID 79 错误出现在内核日志中

**原因：**

- PCIe 链路不稳定（服务器散热、电源问题）
- 硬件故障（GPU 本身损坏）
- 驱动崩溃

**影响：** 使用该 GPU 的所有容器立即失败，训练任务中断

### 2. 链路故障（多卡训练杀手）

**现象：**

- NVLink 带宽下降
- XID 74 错误（NVLink 训练/初始化错误）
- 多 GPU 通信性能显著降低

**原因：**

- NVLink 物理连接问题
- Fabric Manager 配置错误
- GPU 拓扑变化

**影响：** 分布式训练性能下降 50% 以上，甚至训练无法收敛

### 3. 内存故障（数据正确性风险）

**现象：**

- XID 92、95 错误（不可纠正的 ECC 错误）
- GPU 内存重映射事件
- 训练 loss 出现 NaN 或异常波动

**原因：**

- 硬件内存缺陷
- 过热
- 电压不稳定

**影响：** 计算结果不可信，训练可能产生错误的模型

### 4. 驱动故障（最常见但易恢复）

**现象：**

- NVML API 调用超时或失败
- 容器运行时报告设备插件错误
- Pod 卡在 ContainerCreating 状态

**原因：**

- 驱动版本不兼容
- 内核模块崩溃
- Device Plugin 重启

**影响：** 新任务无法调度到该节点，但通常重启服务即可恢复

## 故障检测方案

### 核心工具：DCGM Exporter

NVIDIA Data Center GPU Manager (DCGM) 是生产环境 GPU 监控的事实标准。

**部署方式：** 通过 NVIDIA GPU Operator 自动部署

**关键指标：**

```text
故障类型          指标名称                              告警阈值
-----------------------------------------------------------------
掉卡             DCGM_FI_DEV_XID_ERRORS               XID=79 出现
链路故障         DCGM_FI_DEV_NVLINK_BANDWIDTH_*       < 基线的 80%
内存错误         DCGM_FI_DEV_ECC_DBE_VOL_TOTAL        > 0（不可纠正）
过热             DCGM_FI_DEV_GPU_TEMP                 > 85°C
功耗异常         DCGM_FI_DEV_POWER_VIOLATION          持续 5 分钟
```

**Prometheus 告警示例：**

```yaml
- alert: GPUCardDropout
  expr: increase(DCGM_FI_DEV_XID_ERRORS{xid="79"}[5m]) > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "GPU 掉卡 - 节点 {{ $labels.node }}"
    
- alert: NVLinkDegraded
  expr: |
    DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL < 
    (DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL offset 1h) * 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "NVLink 带宽下降 - GPU {{ $labels.gpu }}"
```

### 辅助工具：Node Problem Detector

用于将 GPU 故障转换为 Kubernetes 原生的 NodeCondition。

**自定义检测脚本示例：**

```bash
#!/bin/bash
# 检查 XID 错误
if dmesg | grep -q "Xid.*79"; then
  echo "GPU_CARD_DROPOUT"
  exit 1
fi

# 检查 nvidia-smi 可用性
if ! nvidia-smi > /dev/null 2>&1; then
  echo "GPU_UNAVAILABLE"
  exit 1
fi

# 检查 NVLink 状态
if nvidia-smi nvlink --status | grep -q "Down"; then
  echo "NVLINK_DOWN"
  exit 1
fi

exit 0
```

**NodeCondition 映射：**

```yaml
status:
  conditions:
  - type: GPUHealthy
    status: "False"
    reason: GPUXIDError
    message: "XID 79 detected on GPU 0"
```

## 三层故障语义模型

将底层硬件信号转换为 Kubernetes 可操作的语义，是自愈的关键。

### 第一层：NodeCondition（节点级）

**用途：** 控制调度器行为，防止新任务被分配到问题节点

**标准 Condition 类型：** （参考微软 AKS）

- `GPUHealthy`: GPU 子系统整体健康状态
- `NVLinkHealthy`: NVLink 连接状态
- `GPUDriverHealthy`: 驱动和 NVML 可用性
- `GPUMemoryHealthy`: ECC 错误在阈值内

**触发动作：**

- 自动添加 Taint: `gpu.health/unhealthy=true:NoSchedule`
- 调度器过滤该节点
- 触发告警通知运维团队

### 第二层：DeviceCondition（设备级）

**用途：** 在多 GPU 节点上隔离单个故障 GPU，避免"整机下线"

**设计思路：** 创建 GPUDevice CRD 追踪每个 GPU 的健康状态

```yaml
apiVersion: gpu.nvidia.com/v1
kind: GPUDevice
metadata:
  name: gpu-node-01-gpu-0
spec:
  uuid: GPU-12345678...
  model: NVIDIA A100-SXM4-80GB
status:
  health:
    status: Unhealthy
    reason: XIDError
    severity: Critical
    confidence: 0.95
  allocatable: false  # 从可分配池中移除
```

**收益：**

- 8 卡节点中 1 卡故障，其他 7 卡仍可用
- 减少"爆炸半径"
- 支持 MIG 场景的细粒度隔离

### 第三层：WorkloadCondition（作业级）

**用途：** 将硬件故障映射到训练框架语义，支持自动重试/恢复

**Volcano Job 集成示例：**

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
status:
  conditions:
  - type: GPUFaultDetected
    status: "True"
    reason: XIDErrorOnPod
    message: "GPU fault on pod worker-3"
  state:
    phase: Requeued  # 自动重新入队
    reason: GPUFaultRemediation
```

**与训练框架集成：**

- Volcano: 支持作业自动 requeue
- Kubeflow Training Operator: 自动替换故障 worker
- PyTorch Elastic: 利用弹性训练机制继续

## 渐进式自愈策略

**核心原则：** 从低影响到高影响逐步升级，每一步都有验证和回滚机制。

### 六级自愈动作

```text
级别  动作                    影响范围        恢复时间    风险
------------------------------------------------------------------
L0   检测告警                无              -           无
L1   Cordon + Taint         新调度阻止      < 1 分钟     极低
L2   重启服务               设备插件重启    1-2 分钟     低
     (device-plugin/
      fabric-manager)
L3   设备隔离               单 GPU 下线     < 1 分钟     低
L4   GPU Reset             使用该 GPU 的    5-10 分钟    中
     (nvidia-smi -r)       容器被杀
L5   Node Drain + Reboot   整个节点下线    10-30 分钟   高
L6   节点替换               节点永久下线    数小时       高
```

### 策略引擎关键要素

**1. 多信号融合（避免误判）**

```text
XID 79 出现 + nvidia-smi 失败 + DCGM 健康检查失败
→ 置信度 0.99 → 立即执行 L1 (Cordon)

ECC 错误数上升但 < 阈值
→ 置信度 0.6 → 仅告警监控
```

**2. 迟滞与冷却（避免抖动）**

- 故障需持续 5 分钟才升级到 Unhealthy
- 执行动作后 30 分钟内不再对同一节点执行相同动作
- 短时 XID 尖峰进入 Suspect 状态观察

**3. 爆炸半径控制（避免雪崩）**

- 每个机架同时最多 10% 节点处于 remediation 状态
- 每个 Availability Zone 限制 5% 节点同时重启
- NVSwitch fabric domain 内限制 1 个节点操作

**4. 工作负载感知**

- 训练任务：更宽松的阈值，优先尝试设备隔离
- 推理服务：更激进的恢复，快速替换 Pod
- 尊重 PodDisruptionBudget 设置

### 集成现有工具

**Draino：** 自动监听 NodeCondition 并执行 drain

```yaml
conditions:
- type: GPUHealthy
  status: "False"
  min-duration: 5m  # 持续 5 分钟才执行 drain
drain-buffer: 10m   # drain 前给应用 10 分钟保存状态
max-concurrent-drains: 3
```

**Node Readiness Controller：** 协调节点进入维护模式

```yaml
maintenance_triggers:
- node_condition:
    type: GPUHealthy
    status: "False"
  action: cordon_and_drain
  grace_period: 5m
```

## 故障感知调度

让调度器"知道"哪些节点更健康，避免新任务被分配到风险节点。

### Scheduler Plugin

**健康度评分算法：**

```text
GPU Health Score = 1.0
  × (1 - 0.4 × XID错误权重)      # 40% 权重
  × (0.7 + 0.3 × NVLink带宽比)  # 30% 权重
  × (1 - 0.2 × ECC错误权重)     # 20% 权重
  × 温度衰减因子                # 10% 权重

最终调度分数 = 健康度评分 × 100
```

**效果：**

- 健康节点（score > 0.9）优先获得关键训练任务
- 中等健康节点（score 0.7-0.9）用于推理或低优先级任务
- 低健康节点（score < 0.7）仅用于可中断任务

### Kueue 集成

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
spec:
  resourceGroups:
  - flavors:
    - name: a100-premium
      nodeSelector:
        gpu.health/score: "0.9"  # 高健康度要求
    - name: a100-standard
      nodeSelector:
        gpu.health/score: "0.7"  # 标准健康度
```

### DRA 健康属性

在 Dynamic Resource Allocation 时代，健康度成为设备选择的一等属性：

```yaml
apiVersion: resource.k8s.io/v1alpha3
kind: ResourceClaim
spec:
  devices:
    requests:
    - deviceClassName: gpu.nvidia.com
      selectors:
      - cel:
          expression: |
            device.health.score > 0.9 &&
            device.health.xidErrors == 0 &&
            device.health.nvlinkStatus == "active"
```

## 作业级归因与计费

**问题：** 是硬件坏了还是作业把硬件"打坏"了？

**解决方案：** DCGM HPC Job Mapping for Kubernetes

### 工作原理

1. **Job Mapping Controller** 监听 Pod 创建事件
2. 查询 kubelet pod-resources API 获取 GPU 分配关系
3. 生成 DCGM 兼容的 mapping 文件：

```text
GPU-12345678-1234-1234-1234-123456789abc,job-12345,training-job-01,ml-team,1702800000
```

1. DCGM Exporter 读取 mapping 文件，为指标添加作业标签

### 增强的指标

```text
# 无 Job Mapping
DCGM_FI_DEV_GPU_UTIL{gpu="0",UUID="GPU-12345..."} 95.0

# 有 Job Mapping
DCGM_FI_DEV_GPU_UTIL{
  gpu="0",
  UUID="GPU-12345...",
  job_name="training-job-01",
  namespace="ml-team",
  pod="training-job-01-worker-0"
} 95.0
```

### 故障归因查询

**哪个作业触发了 XID 错误？**

```promql
increase(DCGM_FI_DEV_XID_ERRORS{job_name!=""}[1h]) > 0
```

**故障发生时的 GPU 利用率？**

```promql
DCGM_FI_DEV_GPU_UTIL{job_name="training-job-01"}
  and on(gpu) increase(DCGM_FI_DEV_XID_ERRORS[5m]) > 0
```

### 公平计费策略

```yaml
故障类型           计费调整     说明
-------------------------------------------------------
硬件故障 (XID 79)   0%        不向用户收费
用户 OOM (XID 13)   100%      全额收费
内存错误 (XID 92)   50%       共同责任（可能是负载过高）
```

## 生产部署建议

### 第一阶段：检测与监控（1-2 周）

- 部署 NVIDIA GPU Operator + DCGM Exporter
- 配置 Prometheus 采集 GPU 指标
- 创建基础告警规则（XID 79, NVLink 降级）
- 部署 Grafana 仪表板可视化

**验证标准：** 能够在 5 分钟内发现并告警 GPU 故障

### 第二阶段：基础自愈（2-4 周）

- 部署 Node Problem Detector + 自定义 GPU 检测脚本
- 部署 Draino 实现自动 drain
- 配置节点替换策略（Cluster Autoscaler）
- 建立人工干预流程（GPU reset / 重启）

**验证标准：** 掉卡故障 30 分钟内自动隔离节点

### 第三阶段：设备级隔离（1-2 月）

- 实现 GPUDevice CRD 和控制器
- 支持单 GPU 隔离（不影响同节点其他 GPU）
- 添加故障验证循环（post-check）
- 实现冷却和限流机制

**验证标准：** 多 GPU 节点单卡故障时，其他 GPU 仍可用

### 第四阶段：故障感知调度（2-3 月）

- 实现 GPU 健康度评分 Scheduler Plugin
- Kueue/Volcano 集成健康度要求
- DRA 驱动添加健康属性
- 实现基于健康度的弹性伸缩

**验证标准：** 关键训练任务避开低健康度节点

### 第五阶段：归因与优化（持续）

- 部署 Job Mapping Controller
- 启用 DCGM HPC Job Mapping
- 实现故障归因报告
- 建立公平计费调整机制

**验证标准：** 能够准确追踪每次 GPU 故障到具体作业

### 运维最佳实践

**1. 保守启动，逐步自动化**

- 第一个月：仅监控告警，人工处理
- 第二个月：启用自动 cordon，人工确认后 drain
- 第三个月：启用完全自动 drain + reboot
- 持续迭代策略参数（阈值、冷却时间）

**2. 建立指标基线**

- 记录每种自愈动作的触发频率
- 跟踪误判率（false positive rate）
- 测量 MTTR（Mean Time To Recovery）改善
- 收集用户反馈（训练中断影响）

**3. 安全防护**

- 所有自愈动作需审计日志
- GPU reset / reboot 需要审批（至少初期）
- 使用 RBAC 限制 remediation controller 权限
- 实现变更通知（Slack / 钉钉）

**4. 与容量规划集成**

- 故障数据输入硬件更换决策
- 预测性维护（ECC 错误累积趋势）
- 机架级故障关联分析（电源、散热）
- 定期演练故障场景

## 参考资料

### 行业实践

**字节跳动火山引擎：**
GPU 故障检测及自愈：大幅提升 AI 场景的硬件故障运维效率
https://mp.weixin.qq.com/s/vc4y2wnZlyou3cfqnQP2-w

**微软 Azure AKS：**
Node Problem Detector 官方文档
https://learn.microsoft.com/en-us/azure/aks/node-problem-detector

### 社区案例

**GPU 掉卡排查实战：**
记录一个有意思的问题的排查过程 -- K8S Pod GPU 卡掉了怎么办?
https://mp.weixin.qq.com/s/ehcX_43lmpaYaQS_x49BcA

**Kubernetes GPU 故障排查：**
在 Kubernetes 集群上的 GPU 掉卡和故障排查
https://nolebase.ayaka.io/zh-CN/笔记/🧱%20基础设施/🚢%20Kubernetes/在%20Kubernetes%20集群上的%20GPU%20掉卡和故障排查.html

**GPU 异常消失处理：**
nvidia-smi GPU异常消失 程序中断
https://www.cnblogs.com/jisongxie/p/10405302.html

### NVIDIA 官方资源

**GPU Debug Guidelines：**
https://docs.nvidia.com/deploy/gpu-debug-guidelines/index.html

**DCGM Exporter：**
https://github.com/NVIDIA/dcgm-exporter

**GPU Operator：**
https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/

**DRA Driver for GPU：**
https://github.com/NVIDIA/k8s-dra-driver-gpu

### Kubernetes 社区

**Node Problem Detector：**
https://github.com/kubernetes/node-problem-detector

**Node Readiness Controller：**
https://github.com/kubernetes-sigs/node-readiness-controller

**Dynamic Resource Allocation：**
https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/

**Draino (自动 drain 工具)：**
https://github.com/planetlabs/draino

### 技术博客

**Kubernetes GPU 可观测性集成：**
https://cloud-atlas.readthedocs.io/zh-cn/latest/kubernetes/gpu/intergrate_gpu_telemetry_into_k8s.html

**DCGM Exporter 源码分析：**
https://www.jianshu.com/p/f38e58864496

---

**完整英文文档：** 更详细的技术实现细节和代码示例，请参考
[GPU Fault Detection and Self-Healing Guide](../../kubernetes/gpu-fault-detection.md)

**最后更新：** 2025-12-17 | **维护者：** pacoxu
