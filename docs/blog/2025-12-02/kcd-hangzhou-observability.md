---
status: Active
maintainer: pacoxu
date: 2025-12-02
tags: observability, prometheus, victoriametrics, fluent-bit, kcd, monitoring
canonical_path: docs/blog/2025-12-02/kcd-hangzhou-observability.md
---

# KCD Hangzhou Hottest Topic: Observability Optimization at Scale

## Overview

At [KCD Hangzhou + OpenInfra Days China 2025](https://sessionize.com/view/cnfxrf60/GridSmart?format=Embed_Styled_Html&isDark=False&title=KCD%20Hangzhou%20%2B%20OpenInfra%20Days%20China%202025),
one of the most popular presentations was Xiaohongshu's (RED) large-scale
metrics monitoring optimization. This post covers their journey to achieve
**10x query speedup** and **save tens of thousands of CPU cores**. We also
connect this to OpenAI's similar observability optimization story from
KubeCon NA 2025.

## Xiaohongshu Large-Scale Metrics Monitoring Optimization

**Speaker**: Zhang Zhengzhong, Observability Engineer at Xiaohongshu

### Resources

- **Slides**: Available at [KCD Hangzhou Sessionize](https://sessionize.com/view/cnfxrf60/GridSmart?format=Embed_Styled_Html&isDark=False&title=KCD%20Hangzhou%20%2B%20OpenInfra%20Days%20China%202025)
- **Video**: [Bilibili Replay](https://www.bilibili.com/video/BV1orUYBVERt)
  (slides in video may be unclear, please download the PPT separately)
- **PDF**: [CloudNative 04 - Xiaohongshu Large-Scale Metrics Monitoring Optimization](https://github.com/user-attachments/files/23870450/CloudNative.04-xiao-hong-shu-da-gui-mo-zhi-biao-jian-kong-you-hua-ti-sheng-10-bei-cha-xun-su-du-jie-yue-mo-he-cpu-zhang-zheng-zhong-.pdf)

### Background and Challenges

**Legacy Architecture:**

- Prometheus deployed separately with each business unit
- VictoriaMetrics as long-term storage
- Thanos providing backup emergency queries

**Problems with Legacy Architecture:**

- **High resource costs**: Prometheus memory usage was high, requiring large
  instance specs and multiple clusters
- **Poor stability**: Failures and changes easily caused data anomalies and
  false alerts
- **High operational costs**: Prometheus deployments were scattered, making
  centralized management impossible; scaling and configuration updates were
  complex and relied heavily on command-line operations
- **Poor user experience**: Query timeouts were common

### Collection Layer Restructuring

**Problem Analysis:**

- High resource costs, large memory requirements, frequent alerts
- Scattered deployments, high operational costs
- Complex configuration management, non-standardized processes

**Restructuring Content:**

- Removed Thanos backup query path
- Secondary development based on vmagent:
  - Integrated configuration center for standardized configuration publishing
  - Collection protection to limit abnormal traffic
  - Centralized management of push metric requirements
- Consolidated collection clusters by business line

**Smooth Scaling:**

- Collection targets distributed across instances by label-based sharding
- Dynamic shard count adjustment enables seamless scaling without downtime

**Performance Optimization:**

| Problem | Solution |
| --- | --- |
| CPU/memory spikes during restarts or adding targets | Batch delayed startup |
| Memory spikes/OOM when deleting many targets | Object pool + concurrency |
| High CPU utilization due to frequent GC | Use GOMEMLIMIT to raise threshold |

**High Availability Improvements:**

**Problem Analysis:**

- Single-replica collection and storage cannot tolerate instance failures;
  data anomalies or complete unavailability during restarts
- No service discovery, relying on static configuration updates
- Under high load, cascading failures were frequent

**High Availability Deployment:**

- **Collection HA**: Dual-replica redundant collection, storage-side dedup
- **Storage HA**: Dual-replica write path, automatic query failover to
  available storage replicas

**Service Discovery:**

| Approach | Description |
| --- | --- |
| Problem | Static address lists were difficult to maintain |
| Transition | Relied on cloud vendor fixed IP capabilities |
| Final Solution | meta-service: adapts to multiple discovery mechanisms |

meta-service supports fallback to manual maintenance and enables automatic
query failover to available storage replicas.

**Smooth Scaling:**

| Problem | Solution |
| --- | --- |
| How to gradually roll out and ensure stability? | Small-traffic index warm-up |

- meta-service sends new shard config to subset of vminsert instances while
  others keep the old config
- After confirming storage load is stable, apply new shard config to all
  traffic

**High Cardinality Governance:**

**High Cardinality Hazards:**

- Incorrect label usage causes series count to explode
- Collection and storage load becomes abnormal or crashes

**Governance Measures:**

- Label-based cardinality limits enabled by default
- Global or metric-level cardinality threshold adjustments for different
  scenarios
- Support for daily/monthly rolling cardinality limits

**High Availability Summary:**

- **Full-path HA**: Tolerates single and multi-instance failures; localized
  failures are transparent to users
- **Cascading failure mitigation**: Cluster unavailability incidents reduced
  from 5 per half-year to 0
- **Dynamic scaling**: Minute-level rapid scaling capability
- **High cardinality governance**: Auto-detect and limit high-cardinality
  metric writes, reducing cluster load by 15%

### Cross-Cloud Multi-Active Deployment

**Background:**

- Evolution from single-cloud single-region to multi-cloud multi-region
- Metrics collection traverses cross-cloud dedicated lines

**Problems:**

- High bandwidth costs for metric transmission over dedicated lines
- Stability risks:
  - Dedicated line failures cause monitoring loss
  - Regional failures make entire monitoring unavailable

**Unit-Based Deployment Solution:**

- Write path deployed in unit-based fashion across major cloud regions
- Query side federates queries across all clusters, auto-detecting and
  tolerating unavailable clusters

**Results:**

- **80% bandwidth cost reduction**: Query traffic bandwidth is far less than
  write traffic
- **Write path isolation**: Not affected by cross-cloud dedicated line outages
- **Regional fault isolation**: Regional failures don't impact monitoring in
  other regions

### Query Optimization

**Slow Query Case Study:**

- Recommendation business dashboard queries were slow, with many timeouts
- Query range was limited: Only recent 1 hour worked; 1-day queries were
  unusable

### Cascading Failures and Resolution

**Symptoms:**

- Brief unavailability of one instance triggered cluster throughput drop,
  unable to self-heal

**Root Cause:**

- Under high load, write rerouting mechanism created a vicious cycle

**Process Analysis:**

1. **Failure triggers reroute**: When some storage nodes become unavailable,
   they're excluded and writes are redistributed to remaining nodes
2. **Redistribution increases load**: New series writes bring index creation
   overhead, further slowing more nodes
3. **Cascading loop**: Slowed nodes stop responding to writes, triggering
   another round of rerouting

**Solution Approach:**

- Keep write sharding fixed, avoid rerouting

**Implementation:**

- **Write-side queuing instead of rerouting**: Each storage node has a
  corresponding disk queue file; queue during failures, replay during recovery
- **Dual-replica switching ensures query data freshness**: Switching triggered
  automatically by meta-service

### Why Were Queries Slow?

**Problem Analysis:**

- **Query process**: Each storage node returns filtered raw metrics, query
  node completes all metric aggregation calculations
- **Large metric volume**: Xiaohongshu recommendation and other business
  scenarios have tens of millions of metric dimensions per business
- **Bottleneck**:
  - Data transfer and computation at query node is proportional to metric volume
  - Single node bandwidth and compute resources are limited, causing high-dimension
    queries to timeout or OOM

### Computation Push-Down Optimization

**Prerequisites:**

- Storage node CPU utilization is low, with buffer capacity
- After HA improvements, series distribution is stable, meeting rate() and
  other window function push-down requirements

**Push-Down Process:**

- **Storage nodes**: Pre-compute intermediate results for sum/min/max and
  other aggregate functions
- **Query nodes**: Receive intermediate results and further aggregate
- **Special handling**: avg and count support push-down with special processing

**Computation Push-Down Results:**

- **Query latency**: 1-day queries reduced to 3 seconds, meeting daily
  inspection needs
- **Query range**: Expanded from 1 day to 7 days

### Further Acceleration: Higher-Dimension Metric Queries

**Pre-Aggregation:**

- Collection side pre-aggregates metrics according to query requirements
- Query side automatically matches and rewrites queries to use pre-aggregated
  metrics, providing transparent acceleration to users
- Pre-aggregation configuration takes effect dynamically in real-time

![Pre-aggregation flow](https://github.com/user-attachments/assets/68e36974-38a8-4010-a491-43ae45397289)

**Pre-Aggregation Results:**

Using gateway HTTP request metrics as an example:

- **Query latency**: All queries complete within 1 second after pre-aggregation
- **Query range**: Easily supports 30-day data queries

### Summary and Outlook

**Achievements:**

- **Stability**: Full-path HA + minute-level elastic scaling
- **Performance**: Collection performance improved nearly 10x, large query
  speed improved by tens of times
- **Cost**: Saved tens of thousands of CPU cores, hundreds of TB SSD,
  80% bandwidth cost reduction
- **Operations**: White-screen operations, no additional daily operational
  manpower needed

**Future Outlook:**

- Capacity operations and auto-scaling
- Support for offline data export

---

## KubeCon NA OpenAI Connection

![KubeCon NA 2025 Keynote](https://github.com/user-attachments/assets/38377d0e-4532-4ac8-953d-e36d2604f39a)

### How One Line of Code Freed 30,000 CPU Cores

**Speaker**: Fabian Ponce, Member of Technical Staff, OpenAI

- **Video**: [YouTube - KubeCon NA 2025 Keynote][kubecon-video]
- **Article**: [The New Stack - OpenAI Fluent Bit Tweak][thenewstack-article]

[kubecon-video]: https://www.youtube.com/watch?v=pbOvWxuYPIU&list=PLj6h78yzYM2MLSW4tUDO2gs2pR5UpiD0C&index=15
[thenewstack-article]: https://thenewstack.io/openai-recovers-30000-cpu-cores-with-fluent-bit-tweak/

### Architecture Overview

In terms of architecture, Fluent Bit generates 10PB of data per day, stored
in [ClickHouse](https://thenewstack.io/moving-from-c-to-rust-clickhouse-has-some-advice/).

![OpenAI Fluent Bit Architecture](https://github.com/user-attachments/assets/dff9aae2-54d0-485e-b0f5-3a537b2faf4d)

### The Discovery

Using [Perf](https://www.brendangregg.com/perf.html) (a Linux tool for
collecting performance data), the observability team analyzed CPU cycles used
by Fluent Bit. Ponce expected that most of Fluent Bit's work would be
preparing and formatting incoming data.

But what surprised Ponce was that this wasn't the case at all. Instead, at
least **35% of CPU cycles** were consumed by a single function (`fstatat64`),
whose purpose was to calculate log file size before reading the log file.

![Fluent Bit inotify change](https://github.com/user-attachments/assets/721f5607-d792-498b-b859-d900b2f8a3d5)

### The Fix

The solution was simple: disable inotify in staging environments and run a
prod experiment on a single cluster. The fix was literally a few lines of
configuration change:

```conf
{% if env == "staging" or cluster_full_name == "prod-engine-aks-s..." %}
    Inotify_Watcher    false
{% endif %}
```

### Key Takeaways

Both Xiaohongshu and OpenAI's stories demonstrate that **observability
optimization can yield massive cost savings**:

| Company | Optimization | Savings |
| --- | --- | --- |
| Xiaohongshu | Metrics monitoring restructuring | 10,000s CPU, 100s TB SSD |
| OpenAI | Fluent Bit inotify disable | 30,000 CPU cores |

The common theme: **profiling and understanding where resources are actually
being consumed** leads to opportunities for significant optimization.

---

## Related Topics

### Tools and Projects Mentioned

- <a href="https://github.com/VictoriaMetrics/VictoriaMetrics">`VictoriaMetrics`</a>:
  Fast and scalable monitoring solution and time series database
- <a href="https://github.com/prometheus/prometheus">`Prometheus`</a>: CNCF
  Graduated. The Prometheus monitoring system and time series database
- <a href="https://github.com/thanos-io/thanos">`Thanos`</a>: CNCF Incubating.
  Highly available Prometheus setup with long term storage capabilities
- <a href="https://github.com/fluent/fluent-bit">`Fluent Bit`</a>: CNCF
  Graduated. Fast and lightweight log processor
- <a href="https://github.com/ClickHouse/ClickHouse">`ClickHouse`</a>:
  Fast open-source column-oriented database management system

### Further Reading

- [Observability Guide](../../observability/README.md)
- [CNCF Observability Landscape](https://landscape.cncf.io/?group=observability-and-analysis)
- [Performance Testing Guide](../../inference/performance-testing.md)

---

**Author**: AI Infrastructure Learning Path  
**Date**: December 2, 2025  
**Tags**: #observability #monitoring #prometheus #victoriametrics #fluent-bit
