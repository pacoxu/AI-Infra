---
status: Active
maintainer: pacoxu
date: 2025-12-02
tags: observability, prometheus, victoriametrics, fluent-bit, kcd, monitoring
canonical_path: docs/blog/2025-12-02/kcd-hangzhou-observability_zh.md
---

# KCD 杭州最热主题：可观测性能优化

## 概述

在 [KCD 杭州 + OpenInfra Days China 2025](https://sessionize.com/view/cnfxrf60/GridSmart?format=Embed_Styled_Html&isDark=False&title=KCD%20Hangzhou%20%2B%20OpenInfra%20Days%20China%202025)
大会上，最受关注的演讲之一是小红书的大规模指标监控优化。本文介绍了他们如何实现**10 倍查询速度
提升**并**节约数万核 CPU**。我们还将这与 KubeCon NA 2025 上 OpenAI 的类似可观测性优化案例
进行关联。

## 小红书大规模指标监控优化

**演讲者**：章正中，小红书可观测技术工程师

### 资源

- **PPT**: 可在 [KCD 杭州 Sessionize][kcd-sessionize] 下载
- **视频**: [Bilibili 回放](https://www.bilibili.com/video/BV1orUYBVERt)
  （视频中 PPT 不太清晰，请结合下载的 PPT 观看）
- **PDF**: [CloudNative 04 - 小红书大规模指标监控优化][pdf-download]

[kcd-sessionize]: https://sessionize.com/view/cnfxrf60/GridSmart?format=Embed_Styled_Html&isDark=False&title=KCD%20Hangzhou%20%2B%20OpenInfra%20Days%20China%202025
[pdf-download]: https://github.com/user-attachments/files/23870450/CloudNative.04-xiao-hong-shu-da-gui-mo-zhi-biao-jian-kong-you-hua-ti-sheng-10-bei-cha-xun-su-du-jie-yue-mo-he-cpu-zhang-zheng-zhong-.pdf

### 背景和挑战

**旧部署架构：**

- Prometheus 随业务分散部署
- VictoriaMetrics 作为长期存储
- Thanos 提供备用应急查询

**旧部署架构遇到的问题：**

- **资源成本高**：Prometheus 内存占用高，实例规格大，集群多
- **稳定性较差**：故障和变更易引发数据异常与告警误报
- **运维成本高**：Prometheus 部署分散，无法集中管理；扩缩容与配置更新流程复杂，依赖大量
  黑屏命令行操作
- **使用体验差**：查询超时

### 采集端重构

**问题梳理：**

- 资源成本高，内存需求大，告警频繁
- 部署分散，运维成本高
- 配置管理繁琐，流程不规范

**重构内容：**

- 移除 Thanos 备用查询链路
- 基于 vmagent 二次开发：
  - 集成配置中心，规范配置发布
  - 采集保护，限制异常流量
  - 集中管控 push 指标需求
- 按业务线收敛采集端集群部署

**平滑扩缩容：**

- 采集对象按标签分片，分配给不同实例
- 分片数动态调整，实现无须停机的平滑扩缩容

**性能优化：**

| 问题 | 解决方案 |
| --- | --- |
| 重启或新增大量采集对象时，CPU/内存剧烈波动 | 分批延迟启动采集 |
| 删除大量采集对象时，内存飙升/OOM | 对象池 + 并发限速 |
| GC 频繁导致的 CPU 利用率高 | 使用 GOMEMLIMIT 提高 GC 阈值，降低 GC 频率 |

![性能优化效果](https://github.com/user-attachments/assets/483edcf4-19df-4c4a-8f22-040f36bfb390)

**高可用改造：**

**问题梳理：**

- 采集与存储单副本，无法容忍单实例异常，重启过程中数据异常或整体不可用
- 缺乏服务发现，依赖静态配置更新
- 高负载情况下，雪崩问题频发

**高可用部署：**

- **采集高可用**：双副本冗余采集，存储端去重
- **存储高可用**：写入链路双副本，查询自动切换可用存储副本

**服务发现：**

| 方案 | 描述 |
| --- | --- |
| 问题 | 静态配置地址列表，维护困难 |
| 过渡方案 | 依赖云厂商提供的固定 IP 能力 |
| 最终方案 | meta-service：适配多种服务发现机制，支持降级到手工维护，支持查询自适应切换可用存储副本 |

**平滑扩缩容：**

| 问题 | 解决方案 |
| --- | --- |
| 扩缩容时，如何灰度，保证存储集群稳定？ | 小流量预热索引 |

- meta-service 选取部分 vminsert 实例下发新的分片配置，其余实例保持不变
- 确认存储负载稳定后，全流量生效新的分片配置

**高基数治理：**

**高基数危害：**

- 错误的 label 使用姿势导致序列数激增
- 采集和存储负载异常甚至崩溃

**治理措施：**

- 默认开启基于 label 基数的管控
- 针对不同场景做全局或者指标级别的基数阈值调整
- 支持按天级月级策略滚动限制基数

**高可用改造总结：**

- **全链路高可用**：具备对单实例、多实例故障的容忍能力，局部故障对用户无感
- **雪崩问题治理**：集群不可用故障从半年 5 次降为 0
- **动态扩缩容**：具备分钟级快速扩缩容能力
- **高基数治理**：可自动感知和限制高基数指标写入，集群负载降低 15%

### 跨云多活部署

**背景：**

- 单云单地域 -> 多云多地域
- 指标采集经过跨云专线

**问题：**

- 指标传输带宽大，专线带宽成本极高
- 存在稳定性风险
  - 专线故障，监控丢失
  - 地域级故障，监控整体不可用

**单元化部署方案：**

- 写入链路在各主要云地域单元化部署
- 查询端联合查询聚合所有集群指标，自动识别并容忍不可用集群

**效果：**

- **带宽成本降低 80%**：查询流量带宽远小于写入
- **写入链路单元化**：不受跨云专线断网影响
- **地域级别故障不影响其他地域监控**

### 查询优化

**慢查询案例：**

- 推荐业务监控大盘，查询缓慢，大量超时
- 可查询范围小：只能支持最近 1 小时，最近一天范围的查询不可用

### 雪崩和解决思路

**现象：**

- 某个实例的短暂不可用引发集群吞吐量下降，无法自愈

**根源：**

- 较高负载下，写入重分片（reroute）机制循环加剧

**过程分析：**

1. **故障触发 reroute**：当部分存储节点不可用时被排除，写入按剩余节点重新分片
2. **重分片加剧负载**：新序列写入带来索引创建的开销，进一步拖慢更多节点
3. **雪崩循环**：被拖慢节点不响应写入，触发新一轮 reroute

**思路：**

- 保持写入分片固定，避免 reroute

**方案：**

- **写入侧积压代替 reroute**：每个存储节点对应一个磁盘队列文件，故障时积压，恢复时回放
- **双副本切换保证查询数据实时性**：切换过程由 meta-service 判断自动触发

### 为什么慢？

**问题分析：**

- **查询过程**：每个存储节点返回过滤匹配得到的原始指标，由查询节点完成所有指标的聚合计算
- **指标量大**：小红书推荐等业务场景单业务指标维度已达千万级别
- **瓶颈**：
  - 查询节点传输数据量与计算量与指标量成正比
  - 单节点带宽和计算资源有限，高维度指标查询超时、OOM

### 计算下推优化

**实现前提：**

- 存储节点 CPU 利用率低，有 buffer
- 高可用改造后，序列分布稳定，满足 rate 等窗口函数的下推计算需求

**下推过程：**

- **存储节点**：对 sum/min/max 等聚合函数预先计算中间结果
- **查询节点**：接收中间结果并进一步聚合
- **特殊处理**：avg 与 count 经过特殊处理支持下推

**计算下推加速效果：**

- **查询耗时**：1 天内查询降低到 3s，满足日常巡检需求
- **查询可用范围**：从 1 天提升到 7 天

### 进一步加速：更高维度的指标查询

**预聚合：**

- 采集侧按查询需求提前聚合指标
- 查询侧自动匹配并改写查询语句，用户无感加速
- 预聚合配置动态实时生效

![预聚合指标写入与查询流程](https://github.com/user-attachments/assets/68e36974-38a8-4010-a491-43ae45397289)

**预聚合加速效果：**

以网关 HTTP 请求指标为例：

- **查询耗时**：预聚合加速后所有查询在 1s 内完成
- **查询可用范围**：轻松支持 30 天数据的查询

### 总结和展望

**成果：**

- **稳定性**：全链路高可用 + 分钟级弹性扩缩容
- **性能**：采集性能提升近 10 倍，大查询速度提升数十倍
- **成本**：节省数万核 CPU、数百 TB SSD，带宽成本降 80%
- **运维**：实现白屏化操作，日常无需额外运维人力

**未来展望：**

- 容量运营与自动扩缩容
- 支持离线数据导出

---

## KubeCon 北美 OpenAI 联动

![KubeCon NA 2025 主题演讲](https://github.com/user-attachments/assets/38377d0e-4532-4ac8-953d-e36d2604f39a)

### 一行代码释放 30,000 核 CPU

**演讲者**：Fabian Ponce，OpenAI 技术人员

- **视频**：[YouTube - KubeCon NA 2025 主题演讲][kubecon-video-zh]
- **文章**：[The New Stack - OpenAI Fluent Bit 调整][thenewstack-article-zh]

[kubecon-video-zh]: https://www.youtube.com/watch?v=pbOvWxuYPIU&list=PLj6h78yzYM2MLSW4tUDO2gs2pR5UpiD0C&index=15
[thenewstack-article-zh]: https://thenewstack.io/openai-recovers-30000-cpu-cores-with-fluent-bit-tweak/

### 架构概述

在架构方面，Fluent Bit 每天生成 10PB 的数据，存储在 [ClickHouse][clickhouse] 上。

[clickhouse]: https://thenewstack.io/moving-from-c-to-rust-clickhouse-has-some-advice/

![OpenAI Fluent Bit 架构](https://github.com/user-attachments/assets/dff9aae2-54d0-485e-b0f5-3a537b2faf4d)

### 发现过程

利用 [Perf](https://www.brendangregg.com/perf.html)（一种用于收集性能数据的 Linux 工具），
可观测性团队分析了 Fluent Bit 使用的 CPU 周期。Ponce 推测，Fluent Bit 大部分工作将是准备
和格式化接收数据。

但让 Ponce 惊讶的是，事实根本不是这样。相反，至少 **35% 的 CPU 周期**被一个函数
（`fstatat64`）处理，该函数的目的是在读取日志文件前计算日志文件的大小。

![Fluent Bit inotify 修改](https://github.com/user-attachments/assets/721f5607-d792-498b-b859-d900b2f8a3d5)

### 解决方案

解决方案非常简单：在 staging 环境禁用 inotify，并在单个生产集群上运行实验。修复实际上只是
几行配置更改：

```conf
{% if env == "staging" or cluster_full_name == "prod-engine-aks-s..." %}
    Inotify_Watcher    false
{% endif %}
```

### 关键启示

小红书和 OpenAI 的案例都表明，**可观测性优化可以带来巨大的成本节约**：

| 公司 | 优化内容 | 节约 |
| --- | --- | --- |
| 小红书 | 指标监控重构 | 数万核 CPU、数百 TB SSD、80% 带宽 |
| OpenAI | 禁用 Fluent Bit inotify | 30,000 核 CPU |

共同主题：**通过性能分析和理解资源实际消耗的位置**，可以发现显著的优化机会。

---

## 相关主题

### 提及的工具和项目

- <a href="https://github.com/VictoriaMetrics/VictoriaMetrics">`VictoriaMetrics`</a>：
  快速、经济高效且可扩展的监控解决方案和时序数据库
- <a href="https://github.com/prometheus/prometheus">`Prometheus`</a>：CNCF
  毕业项目。Prometheus 监控系统和时序数据库
- <a href="https://github.com/thanos-io/thanos">`Thanos`</a>：CNCF 孵化项目。
  具有长期存储能力的高可用 Prometheus 设置
- <a href="https://github.com/fluent/fluent-bit">`Fluent Bit`</a>：CNCF
  毕业项目。快速轻量的日志处理器
- <a href="https://github.com/ClickHouse/ClickHouse">`ClickHouse`</a>：
  快速开源的列式数据库管理系统

### 延伸阅读

- [可观测性指南](../../observability/README.md)
- [CNCF 可观测性全景图](https://landscape.cncf.io/?group=observability-and-analysis)
- [性能测试指南](../../inference/performance-testing.md)

---

**作者**：AI 基础设施学习路径  
**日期**：2025 年 12 月 2 日  
**标签**：#可观测性 #监控 #prometheus #victoriametrics #fluent-bit
